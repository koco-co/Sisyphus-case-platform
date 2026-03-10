# Sisyphus-Y 综合增强实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 修复工作台消息内嵌用例渲染、构建历史 CSV 清洗管线、增强 AI 模型配置页面、重写 progress.json。

**Architecture:** 后端采用 FastAPI + SQLAlchemy 2.0 异步模式，引擎层统一管理 LLM 调用。前端 Next.js App Router + Zustand 状态管理。CSV 清洗通过 Celery 异步批处理，LLM 使用 GLM-4-Flash。API Key 加密存储使用 Fernet 对称加密。

**Tech Stack:** Python 3.12 / FastAPI / SQLAlchemy 2.0 / Celery / Next.js 16 / TypeScript / Zustand / Tailwind CSS / Qdrant / PostgreSQL

**Design Doc:** `docs/plans/2026-03-10-comprehensive-enhancement-design.md`

---

## Phase 1: 工作台消息内嵌用例修复 (P0)

### Task 1: 后端 — messages 接口返回关联用例数据

**问题：** `GET /generation/sessions/{id}/messages` 只返回 `id, role, content, thinking_content, created_at`，不返回 `cases` 字段。前端 ChatArea 的 `message.cases` 始终为空。

**Files:**
- Modify: `backend/app/modules/generation/router.py:94-106`
- Modify: `backend/app/modules/generation/service.py:139-149`
- Test: `tests/unit/test_generation/test_messages_with_cases.py`

**Step 1: Write the failing test**

```python
# tests/unit/test_generation/test_messages_with_cases.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.modules.generation.service import GenerationService


@pytest.fixture
def mock_session():
    return AsyncMock()


@pytest.fixture
def service(mock_session):
    return GenerationService(mock_session)


async def test_list_messages_with_cases_returns_cases(service, mock_session):
    """Messages listing should include associated test cases."""
    session_id = uuid4()
    msg_id = uuid4()

    # Mock message
    mock_msg = MagicMock()
    mock_msg.id = msg_id
    mock_msg.role = "assistant"
    mock_msg.content = "Generated test cases"
    mock_msg.thinking_content = None
    mock_msg.created_at = None

    # Mock case
    mock_case = MagicMock()
    mock_case.id = uuid4()
    mock_case.case_id = "TC-001"
    mock_case.title = "Test case 1"
    mock_case.priority = "P0"
    mock_case.case_type = "functional"
    mock_case.status = "draft"
    mock_case.steps = [{"step_num": 1, "action": "Click", "expected_result": "OK"}]
    mock_case.ai_score = 0.9
    mock_case.precondition = "User logged in"
    mock_case.created_at = None

    # Stub DB queries
    msg_result = MagicMock()
    msg_result.scalars.return_value.all.return_value = [mock_msg]
    case_result = MagicMock()
    case_result.scalars.return_value.all.return_value = [mock_case]
    mock_session.execute = AsyncMock(side_effect=[msg_result, case_result])

    messages = await service.list_messages_with_cases(session_id)

    assert len(messages) == 1
    assert messages[0]["cases"] is not None
```

**Step 2: Run test to verify it fails**

```bash
cd backend && uv run pytest tests/unit/test_generation/test_messages_with_cases.py -v
```
Expected: FAIL — `GenerationService` has no `list_messages_with_cases` method.

**Step 3: Implement `list_messages_with_cases` in service**

Add to `backend/app/modules/generation/service.py` after `list_messages()` (after line 149):

```python
async def list_messages_with_cases(self, session_id: UUID) -> list[dict]:
    """Return messages with associated test cases for each assistant message."""
    messages = await self.list_messages(session_id)
    cases = await self.list_session_cases(session_id)

    result = []
    for msg in messages:
        msg_dict = {
            "id": str(msg.id),
            "role": msg.role,
            "content": msg.content,
            "thinking_content": msg.thinking_content,
            "created_at": msg.created_at.isoformat() if msg.created_at else "",
            "cases": None,
        }
        if msg.role == "assistant":
            msg_created = msg.created_at
            next_user_msgs = [
                m for m in messages
                if m.role == "user" and m.created_at and msg_created and m.created_at > msg_created
            ]
            cutoff = next_user_msgs[0].created_at if next_user_msgs else None

            matched_cases = []
            for c in cases:
                if c.created_at and msg_created and c.created_at >= msg_created:
                    if cutoff is None or c.created_at <= cutoff:
                        matched_cases.append(c)

            if matched_cases:
                msg_dict["cases"] = [
                    {
                        "id": str(c.id),
                        "case_id": c.case_id,
                        "title": c.title,
                        "priority": c.priority,
                        "case_type": c.case_type if c.case_type != "functional" else "normal",
                        "status": c.status,
                        "steps": [
                            {
                                "no": s.get("step_num", s.get("step", i + 1)),
                                "action": s.get("action", ""),
                                "expected_result": s.get("expected_result", s.get("expected", "")),
                            }
                            for i, s in enumerate(c.steps or [])
                        ],
                        "ai_score": c.ai_score,
                        "precondition": c.precondition,
                    }
                    for c in matched_cases
                ]
        result.append(msg_dict)
    return result
```

**Step 4: Update router to use new method**

Modify `backend/app/modules/generation/router.py` lines 94-106:

```python
@router.get("/sessions/{session_id}/messages")
async def list_messages(session_id: uuid.UUID, session: AsyncSessionDep) -> list[dict]:
    svc = GenerationService(session)
    return await svc.list_messages_with_cases(session_id)
```

**Step 5: Run test to verify it passes**

```bash
cd backend && uv run pytest tests/unit/test_generation/test_messages_with_cases.py -v
```
Expected: PASS

**Step 6: Commit**

```bash
git add backend/app/modules/generation/service.py backend/app/modules/generation/router.py tests/unit/test_generation/test_messages_with_cases.py
git commit -m "feat(generation): return associated test cases in messages endpoint

Messages listing now includes matched TestCase data for each assistant
message, enabling inline CaseCard rendering in ChatArea.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 2: 前端 — 验证 CaseCard 渲染通路

**问题：** 后端修复后需确认前端 `ChatArea.tsx` 的 `message.cases` → `CaseCard` 渲染链路正常工作。

**Files:**
- Verify: `frontend/src/app/(main)/workbench/_components/ChatArea.tsx:95-109`
- Verify: `frontend/src/components/workspace/CaseCard.tsx`
- Modify: `frontend/src/stores/workspace-store.ts` (如有 type 不匹配)

**Step 1: 检查类型一致性**

后端返回的 case 结构中 steps 用 `no` 字段（与 CaseCard 的 `TestCaseStep.no` 匹配），`case_type` 对 "functional" 映射为 "normal"。确认 `WorkbenchMessage.cases` 类型中 steps 使用 `no` 字段。

查看 `frontend/src/stores/workspace-store.ts:30-31`:
```typescript
steps: { no: number; action: string; expected_result: string }[];
```
类型已匹配，无需修改。

**Step 2: 确认 CaseCard 接口兼容**

查看 `CaseCard.tsx:7-11`：
```typescript
interface TestCaseStep {
  no: number;
  action: string;
  expected_result: string;
}
```
匹配。CaseCard 的 `steps` 渲染逻辑使用 `step.no` 和 `step.action`，与后端返回结构一致。

**Step 3: 确认 precondition 字段展示**

当前 CaseCard 不展示 `precondition`。根据原型图（line 3338），需要展示前置条件。

修改 `frontend/src/components/workspace/CaseCard.tsx`：

在 CaseCardProps 接口中增加 `precondition?: string`：
```typescript
interface CaseCardProps {
  caseId: string;
  title: string;
  priority: 'P0' | 'P1' | 'P2' | 'P3';
  type?: string;
  status?: string;
  precondition?: string;  // 新增
  steps: TestCaseStep[];
  aiScore?: number;
  className?: string;
}
```

在 Title 下方、AI Score 上方插入前置条件渲染：
```tsx
{/* Precondition */}
{precondition && (
  <p className="text-[11px] text-text3 mb-2">
    前置：{precondition}
  </p>
)}
```

**Step 4: 更新 ChatArea 和 GeneratedCases 传入 precondition**

`ChatArea.tsx` line 102 添加 `precondition={tc.precondition}`：
```tsx
<CaseCard
  key={tc.id}
  caseId={tc.case_id}
  title={tc.title}
  priority={tc.priority}
  type={tc.case_type}
  status={tc.status}
  precondition={tc.precondition}
  steps={tc.steps}
  aiScore={tc.ai_score}
/>
```

同样更新 `GeneratedCases.tsx` line 73-82 传入 `precondition`。

同时更新 `WorkbenchTestCase` 类型增加 `precondition` 字段：
```typescript
// workspace-store.ts
export interface WorkbenchTestCase {
  // ... existing fields ...
  precondition?: string;  // 新增
}
```

**Step 5: 类型检查**

```bash
cd frontend && bunx tsc --noEmit
```
Expected: 无错误

**Step 6: Commit**

```bash
git add frontend/src/components/workspace/CaseCard.tsx frontend/src/app/(main)/workbench/_components/ChatArea.tsx frontend/src/app/(main)/workbench/_components/GeneratedCases.tsx frontend/src/stores/workspace-store.ts
git commit -m "feat(workbench): add precondition display to CaseCard and wire cases data flow

CaseCard now shows precondition text. ChatArea and GeneratedCases pass
precondition prop. WorkbenchTestCase type updated to include precondition.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

## Phase 2: progress.json 重写

### Task 3: 重写 progress.json 为细粒度任务清单

**Files:**
- Modify: `progress.json`

**Step 1: 生成新的 progress.json**

清空现有内容，按新格式生成完整任务列表。任务范围覆盖：
- P0 工作台主链路 (TASK-001 ~ TASK-010)
- P0 历史数据清洗主链路 (TASK-011 ~ TASK-030)
- P1 AI 模型配置 (TASK-031 ~ TASK-045)
- P1 其余功能 (TASK-046+)

每个任务包含：id, module, title, description, acceptance, files, depends_on, status

**Step 2: 验证 JSON 格式合法**

```bash
python -c "import json; json.load(open('progress.json'))" && echo "Valid JSON"
```

**Step 3: Commit**

```bash
git add progress.json
git commit -m "chore: rewrite progress.json with granular task breakdown

158 tasks across 4 priority groups with acceptance criteria and
file references. Replaces phase-based format with flat task list.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

## Phase 3: CSV 历史用例清洗管线 (P0)

### Task 4: 数据库模型扩展 — TestCase 增加清洗字段

**Files:**
- Modify: `backend/app/modules/testcases/models.py`
- Create: Alembic migration

**Step 1: 添加字段到 TestCase 模型**

在 `backend/app/modules/testcases/models.py` TestCase 类末尾添加：

```python
clean_status: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
quality_score: Mapped[float | None] = mapped_column(nullable=True)
original_raw: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
```

`clean_status` 枚举：`'excellent'` (4.5-5) / `'good'` (3.5-4.4) / `'polished'` (润色后达标) / `'discarded'` (丢弃)

**Step 2: 生成 Alembic 迁移**

```bash
cd backend && uv run alembic revision --autogenerate -m "add clean_status quality_score original_raw to test_cases"
```

**Step 3: 执行迁移**

```bash
cd backend && uv run alembic upgrade head
```

**Step 4: Commit**

```bash
git add backend/app/modules/testcases/models.py backend/alembic/versions/
git commit -m "feat(testcases): add clean_status, quality_score, original_raw fields

Supports imported case quality tracking and before/after comparison.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 5: LLM 清洗引擎 — 核心 Prompt 与清洗逻辑

**Files:**
- Create: `backend/app/engine/import_clean/cleaner.py`
- Test: `tests/unit/test_import_clean/test_cleaner.py`

**Step 1: Write the failing test**

```python
# tests/unit/test_import_clean/test_cleaner.py
import pytest
from app.engine.import_clean.cleaner import (
    strip_html_tags,
    normalize_empty_values,
    score_test_case,
)


def test_strip_html_tags():
    assert strip_html_tags("<p>hello</p>") == "hello"
    assert strip_html_tags("<br/>line<br>break") == "\nline\nbreak"
    assert strip_html_tags("<span style='color:red'>text</span>") == "text"


def test_normalize_empty_values():
    assert normalize_empty_values("无") == ""
    assert normalize_empty_values("-") == ""
    assert normalize_empty_values("null") == ""
    assert normalize_empty_values(None) == ""
    assert normalize_empty_values("valid content") == "valid content"


def test_score_test_case_high_quality():
    case = {
        "title": "验证 MySQL 数据源连接超时的重试机制",
        "precondition": "数据库类型：MySQL 8.0\n建表语句：CREATE TABLE test (id INT)",
        "steps": [
            {"action": "进入 数据中台 > 数据源管理 页面", "expected_result": "页面正常加载"},
            {"action": "点击测试连接按钮", "expected_result": "显示连接超时提示"},
        ],
    }
    score = score_test_case(case)
    assert score >= 3.5


def test_score_test_case_low_quality():
    case = {
        "title": "",
        "precondition": "",
        "steps": [],
    }
    score = score_test_case(case)
    assert score < 2.0
```

**Step 2: Run test to verify it fails**

```bash
cd backend && uv run pytest tests/unit/test_import_clean/test_cleaner.py -v
```

**Step 3: Implement the cleaner module**

```python
# backend/app/engine/import_clean/cleaner.py
"""LLM-assisted test case cleaning engine."""

import json
import logging
import re

from app.ai.llm_client import invoke_llm

logger = logging.getLogger(__name__)

# ── HTML 标签处理 ──

def strip_html_tags(text: str) -> str:
    """Remove HTML tags from text, converting <br> to newlines."""
    if not text:
        return ""
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()


def normalize_empty_values(value: str | None) -> str:
    """Normalize null-like values to empty string."""
    if value is None:
        return ""
    v = str(value).strip()
    if v.lower() in ("无", "-", "null", "none", "n/a", "nan", ""):
        return ""
    return v


# ── 质量评分 ──

def score_test_case(case: dict) -> float:
    """Score a test case from 0.0 to 5.0 based on completeness and quality."""
    score = 0.0
    title = case.get("title", "")
    precondition = case.get("precondition", "")
    steps = case.get("steps", [])

    # Title quality (0-1.5)
    if title:
        score += 0.5
        if len(title) >= 10:
            score += 0.5
        if any(kw in title for kw in ("验证", "校验", "检查", "确认")):
            score += 0.5

    # Steps quality (0-2.0)
    if steps:
        score += 0.5
        valid_steps = [s for s in steps if s.get("action")]
        if len(valid_steps) >= 2:
            score += 0.5
        steps_with_expected = [s for s in steps if s.get("expected_result")]
        if len(steps_with_expected) == len(valid_steps) and valid_steps:
            score += 0.5
        first_action = valid_steps[0].get("action", "") if valid_steps else ""
        if "进入" in first_action or "打开" in first_action:
            score += 0.5

    # Precondition quality (0-1.0)
    if precondition:
        score += 0.5
        if len(precondition) >= 20:
            score += 0.5

    # No vague expressions bonus (0-0.5)
    all_text = f"{title} {precondition} {' '.join(s.get('action', '') for s in steps)}"
    vague_words = ["正确地", "合理地", "正常", "操作成功", "显示正确", "无报错"]
    if not any(w in all_text for w in vague_words):
        score += 0.5

    return min(score, 5.0)


# ── LLM 清洗 ──

CLEAN_SYSTEM_PROMPT = """你是测试用例清洗专家。你的任务是将粗糙的测试用例清洗为规范、可执行的高质量用例。

## 清洗规则

### 前置条件规则
- 如果涉及数据库操作，必须补全：数据库类型、建表语句(CREATE TABLE)、测试数据(INSERT INTO)、初始状态
- 如果不涉及数据库，描述清楚系统初始状态（如"用户已登录"、"功能已开启"）

### 步骤规则
- 第一步必须是：进入 [完整页面路径] 页面（如：数据中台 > 数据源管理 > MySQL数据源列表）
- 每条用例必须独立可执行，不得依赖其他用例
- 禁止出现"正确地"、"合理地"等模糊形容词
- 禁止出现"参考用例XXX"、"在上一步基础上"等依赖描述

### 预期结果规则
- 每个步骤必须有至少一个预期结果
- 一个步骤多个预期时格式为：1) xxx 2) xxx 3) xxx
- 预期必须具体可验证，禁止"操作成功"、"显示正确"、"无报错"

## 输出格式（严格JSON）
```json
{
  "title": "清洗后的标题",
  "precondition": "清洗后的前置条件",
  "steps": [
    {"action": "步骤描述", "expected_result": "预期结果"}
  ]
}
```
只输出JSON，不要其他文字。"""


async def llm_clean_case(raw_case: dict, module_path: str = "") -> dict | None:
    """Clean a single test case using LLM."""
    user_prompt = f"""请清洗以下测试用例：

模块路径：{module_path}
标题：{raw_case.get('title', '')}
前置条件：{raw_case.get('precondition', '')}
步骤：{raw_case.get('steps', '')}
预期结果：{raw_case.get('expected_result', '')}
优先级：{raw_case.get('priority', '')}"""

    try:
        result = await invoke_llm(
            messages=[
                {"role": "system", "content": CLEAN_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            provider="zhipu",
            max_retries=2,
        )

        match = re.search(r"\{.*\}", result.content, re.DOTALL)
        if not match:
            logger.warning("LLM returned non-JSON for case: %s", raw_case.get("title", ""))
            return None

        return json.loads(match.group())
    except Exception:
        logger.exception("LLM clean failed for case: %s", raw_case.get("title", ""))
        return None


async def llm_clean_batch(cases: list[dict], module_path: str = "") -> list[dict | None]:
    """Clean a batch of test cases."""
    results = []
    for case in cases:
        cleaned = await llm_clean_case(case, module_path)
        results.append(cleaned)
    return results
```

**Step 4: Run tests**

```bash
cd backend && uv run pytest tests/unit/test_import_clean/test_cleaner.py -v
```
Expected: PASS (pure function tests, no LLM calls)

**Step 5: Commit**

```bash
git add backend/app/engine/import_clean/cleaner.py tests/unit/test_import_clean/
git commit -m "feat(import_clean): add LLM-powered test case cleaning engine

Includes HTML tag stripping, empty value normalization, quality scoring,
and GLM-4-Flash powered cleaning with structured prompts.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 6: CSV 批量解析 — 统一 65 个文件的列格式

**Files:**
- Create: `backend/app/engine/import_clean/batch_parser.py`
- Test: `tests/unit/test_import_clean/test_batch_parser.py`

**Step 1: Write the failing test**

```python
# tests/unit/test_import_clean/test_batch_parser.py
import pytest
from app.engine.import_clean.batch_parser import (
    normalize_csv_row,
    extract_module_from_path,
)


def test_normalize_csv_row_25_columns():
    """数栈平台格式（25列）应正确提取关键字段。"""
    row = {
        "用例标题": "验证minio accesskey异常",
        "前置条件": "<p>无</p>",
        "步骤": "1. 进入控制台\n2. 输入错误key",
        "预期": "1. 保存成功\n2. 联通性失败",
        "优先级": "3",
        "所属模块": "/公共组件/MinIO(#9283)",
    }
    result = normalize_csv_row(row)
    assert result["title"] == "验证minio accesskey异常"
    assert "<p>" not in result["precondition"]
    assert result["priority"] in ("P0", "P1", "P2", "P3")
    assert len(result["steps_raw"]) > 0


def test_normalize_csv_row_9_columns():
    """信永中和格式（9列）应正确提取。"""
    row = {
        "用例标题": "流程列表验证功能正常",
        "前置条件": "无",
        "步骤": "1. 选择记录, 检查详情页",
        "预期": "1. 详情页显示正确",
        "优先级": "2",
        "所属模块": "【0208版本】流程中心",
    }
    result = normalize_csv_row(row)
    assert result["title"] == "流程列表验证功能正常"
    assert result["precondition"] == ""
    assert result["priority"] == "P2"


def test_extract_module_from_path():
    assert extract_module_from_path("待清洗数据/数栈平台/公共组件_STD/file.csv") == ("数栈平台", "公共组件_STD")
    assert extract_module_from_path("待清洗数据/信永中和/file.csv") == ("信永中和", "")
```

**Step 2: Run test → FAIL**

```bash
cd backend && uv run pytest tests/unit/test_import_clean/test_batch_parser.py -v
```

**Step 3: Implement batch_parser.py**

```python
# backend/app/engine/import_clean/batch_parser.py
"""Batch CSV parser for legacy test case files."""

import csv
import io
import logging
import os
from pathlib import Path

from app.engine.import_clean.cleaner import normalize_empty_values, strip_html_tags

logger = logging.getLogger(__name__)

# 优先级映射：禅道数值 → 标准优先级
PRIORITY_MAP = {"1": "P0", "2": "P1", "3": "P2", "4": "P3"}

# 列名别名映射
COLUMN_ALIASES = {
    "title": ["用例标题", "用例名称", "标题"],
    "precondition": ["前置条件", "前提条件"],
    "steps": ["步骤", "操作步骤", "测试步骤"],
    "expected": ["预期", "预期结果", "期望结果"],
    "priority": ["优先级"],
    "module": ["所属模块", "模块"],
}


def _resolve_column(row: dict, aliases: list[str]) -> str:
    """Find the first matching column from alias list."""
    for alias in aliases:
        if alias in row:
            return str(row[alias] or "")
    return ""


def normalize_csv_row(row: dict) -> dict:
    """Normalize a single CSV row to standard format."""
    title = strip_html_tags(normalize_empty_values(_resolve_column(row, COLUMN_ALIASES["title"])))
    precondition = strip_html_tags(normalize_empty_values(_resolve_column(row, COLUMN_ALIASES["precondition"])))
    steps_raw = strip_html_tags(normalize_empty_values(_resolve_column(row, COLUMN_ALIASES["steps"])))
    expected_raw = strip_html_tags(normalize_empty_values(_resolve_column(row, COLUMN_ALIASES["expected"])))
    priority_raw = normalize_empty_values(_resolve_column(row, COLUMN_ALIASES["priority"]))
    module = normalize_empty_values(_resolve_column(row, COLUMN_ALIASES["module"]))

    priority = PRIORITY_MAP.get(priority_raw, "P2")

    return {
        "title": title,
        "precondition": precondition,
        "steps_raw": steps_raw,
        "expected_raw": expected_raw,
        "priority": priority,
        "module": module,
        "original_row": row,
    }


def extract_module_from_path(file_path: str) -> tuple[str, str]:
    """Extract product and module from directory path.

    Returns (product_name, module_name).
    Example: "待清洗数据/数栈平台/公共组件_STD/file.csv" → ("数栈平台", "公共组件_STD")
    """
    parts = Path(file_path).parts
    try:
        idx = parts.index("待清洗数据")
    except ValueError:
        return ("", "")

    remaining = parts[idx + 1 :]
    product = remaining[0] if len(remaining) > 0 else ""
    # Skip the filename itself
    module = remaining[1] if len(remaining) > 2 else ""
    # Remove trailing _STD if present in display
    return (product, module)


def parse_csv_file(file_path: str, encoding: str = "utf-8-sig") -> list[dict]:
    """Parse a single CSV file and normalize all rows."""
    results = []
    product, module = extract_module_from_path(file_path)

    with open(file_path, encoding=encoding, errors="replace") as f:
        reader = csv.DictReader(f)
        for row_num, row in enumerate(reader, start=2):
            normalized = normalize_csv_row(row)
            if not normalized["title"]:
                continue
            normalized["product"] = product
            normalized["module_group"] = module
            normalized["source_file"] = os.path.basename(file_path)
            normalized["row_number"] = row_num
            results.append(normalized)

    logger.info("Parsed %d rows from %s", len(results), file_path)
    return results


def discover_csv_files(base_dir: str) -> list[str]:
    """Recursively discover all CSV files under base_dir."""
    csv_files = []
    for root, _dirs, files in os.walk(base_dir):
        for f in sorted(files):
            if f.lower().endswith(".csv"):
                csv_files.append(os.path.join(root, f))
    return csv_files
```

**Step 4: Run tests → PASS**

```bash
cd backend && uv run pytest tests/unit/test_import_clean/test_batch_parser.py -v
```

**Step 5: Commit**

```bash
git add backend/app/engine/import_clean/batch_parser.py tests/unit/test_import_clean/test_batch_parser.py
git commit -m "feat(import_clean): add batch CSV parser with column normalization

Handles both 25-column (数栈平台) and 9-column (信永中和) CSV formats.
Strips HTML tags, normalizes priorities, extracts product/module from path.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 7: Celery 清洗任务 — 批处理编排

**Files:**
- Create: `backend/app/modules/import_clean/tasks.py`
- Modify: `backend/app/modules/import_clean/router.py` (添加触发端点)
- Modify: `backend/app/modules/import_clean/schemas.py` (添加请求/响应模型)

**Step 1: Create Celery task**

```python
# backend/app/modules/import_clean/tasks.py
"""Celery tasks for batch CSV cleaning."""

import asyncio
import logging
import uuid

from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="clean_csv_batch")
def clean_csv_batch_task(self, base_dir: str, batch_size: int = 10):
    """Discover and clean all CSV files in base_dir."""
    return asyncio.run(_clean_csv_batch_async(self, base_dir, batch_size))


async def _clean_csv_batch_async(task, base_dir: str, batch_size: int):
    from app.core.database import get_async_session_context
    from app.engine.import_clean.batch_parser import discover_csv_files, parse_csv_file
    from app.engine.import_clean.cleaner import llm_clean_case, score_test_case
    from app.modules.testcases.service import TestCaseService
    from app.modules.testcases.schemas import TestCaseCreate, TestCaseStepSchema

    csv_files = discover_csv_files(base_dir)
    total_files = len(csv_files)
    stats = {"total_rows": 0, "cleaned": 0, "discarded": 0, "errors": 0}

    for file_idx, file_path in enumerate(csv_files):
        rows = parse_csv_file(file_path)
        stats["total_rows"] += len(rows)

        for batch_start in range(0, len(rows), batch_size):
            batch = rows[batch_start : batch_start + batch_size]

            for row in batch:
                try:
                    cleaned = await llm_clean_case(row, module_path=row.get("module", ""))
                    if not cleaned:
                        stats["errors"] += 1
                        continue

                    cleaned_with_meta = {**cleaned, "priority": row["priority"]}
                    quality = score_test_case(cleaned_with_meta)

                    if quality < 2.0:
                        stats["discarded"] += 1
                        continue

                    clean_status = "excellent" if quality >= 4.5 else "good" if quality >= 3.5 else "polished"

                    steps = [
                        TestCaseStepSchema(
                            step=i + 1,
                            action=s.get("action", ""),
                            expected=s.get("expected_result", ""),
                        )
                        for i, s in enumerate(cleaned.get("steps", []))
                    ]

                    async with get_async_session_context() as session:
                        # Need a valid requirement_id — use or create a placeholder
                        tc_svc = TestCaseService(session)
                        case_data = TestCaseCreate(
                            requirement_id=uuid.UUID("00000000-0000-0000-0000-000000000000"),
                            title=cleaned.get("title", row["title"]),
                            precondition=cleaned.get("precondition", ""),
                            priority=row["priority"],
                            case_type="functional",
                            source="imported",
                            steps=steps,
                        )
                        tc = await tc_svc.create_case(case_data)
                        # Update clean-specific fields
                        tc.clean_status = clean_status
                        tc.quality_score = quality
                        tc.original_raw = row.get("original_row")
                        tc.module_path = f"{row.get('product', '')}/{row.get('module_group', '')}"
                        await session.commit()

                    stats["cleaned"] += 1

                except Exception:
                    logger.exception("Failed to clean row: %s", row.get("title", ""))
                    stats["errors"] += 1

            # Update task progress
            progress = (file_idx * 100) // total_files
            task.update_state(state="PROGRESS", meta={"progress": progress, **stats})

    return stats
```

**Step 2: Add trigger endpoint to router**

Add to `backend/app/modules/import_clean/router.py`:

```python
@router.post("/batch-clean")
async def trigger_batch_clean(base_dir: str = "待清洗数据"):
    """Trigger async batch cleaning of all CSV files."""
    from app.modules.import_clean.tasks import clean_csv_batch_task
    task = clean_csv_batch_task.delay(base_dir)
    return {"task_id": task.id, "status": "started"}


@router.get("/batch-clean/{task_id}")
async def get_batch_clean_status(task_id: str):
    """Check batch cleaning task progress."""
    from app.core.celery_app import celery_app
    result = celery_app.AsyncResult(task_id)
    return {
        "task_id": task_id,
        "status": result.status,
        "result": result.result if result.ready() else result.info,
    }
```

**Step 3: Commit**

```bash
git add backend/app/modules/import_clean/tasks.py backend/app/modules/import_clean/router.py
git commit -m "feat(import_clean): add Celery batch cleaning task with progress tracking

Orchestrates CSV discovery → parsing → LLM cleaning → quality scoring →
PostgreSQL persistence. Exposes trigger and status check endpoints.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 8: Qdrant 向量化 — 清洗后用例写入向量库

**Files:**
- Modify: `backend/app/modules/import_clean/tasks.py` (添加向量化步骤)
- Modify: `backend/app/engine/rag/retriever.py` (确保 collection 支持自定义)

**Step 1: 在清洗任务完成后添加向量化逻辑**

在 `_clean_csv_batch_async` 的每条用例持久化到 PG 后，调用向量化：

```python
# 在 tc 创建成功后追加:
from app.engine.rag.embedder import embed_texts
from app.engine.rag.retriever import ensure_collection, COLLECTION_NAME
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from app.core.config import get_settings

settings = get_settings()
vector_text = f"{cleaned.get('title', '')} {cleaned.get('precondition', '')} {' '.join(s.get('action', '') for s in cleaned.get('steps', []))}"
vectors = await embed_texts([vector_text])
if vectors:
    client = QdrantClient(url=settings.qdrant_url)
    ensure_collection()
    client.upsert(
        collection_name="sisyphus_cleaned_cases",
        points=[
            PointStruct(
                id=str(tc.id),
                vector=vectors[0],
                payload={
                    "case_id": tc.case_id,
                    "product": row.get("product", ""),
                    "module": row.get("module_group", ""),
                    "priority": row["priority"],
                    "quality_score": quality,
                },
            )
        ],
    )
```

**Step 2: Commit**

```bash
git add backend/app/modules/import_clean/tasks.py
git commit -m "feat(import_clean): add Qdrant vectorization for cleaned cases

Each cleaned case is embedded and indexed in sisyphus_cleaned_cases
collection with product/module/priority/quality metadata.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 9: 前端 — 用例管理页增加"已导入"筛选和清洗对比视图

**Files:**
- Modify: `frontend/src/app/(main)/testcases/page.tsx`
- Create: `frontend/src/app/(main)/testcases/_components/CleanCompare.tsx`

**Step 1: 添加 source='imported' 筛选**

在 `testcases/page.tsx` 的 source 筛选选项中添加 `imported`（应该已有，确认即可）。

**Step 2: 创建清洗对比组件**

```tsx
// frontend/src/app/(main)/testcases/_components/CleanCompare.tsx
'use client';

import { useState } from 'react';

interface CleanCompareProps {
  originalRaw: Record<string, unknown> | null;
  cleanedTitle: string;
  cleanedPrecondition: string;
  cleanedSteps: { action: string; expected_result: string }[];
  qualityScore: number | null;
  cleanStatus: string | null;
}

const STATUS_COLORS: Record<string, string> = {
  excellent: 'text-sy-accent bg-sy-accent/10',
  good: 'text-sy-info bg-sy-info/10',
  polished: 'text-sy-warn bg-sy-warn/10',
  discarded: 'text-sy-danger bg-sy-danger/10',
};

export function CleanCompare({
  originalRaw,
  cleanedTitle,
  cleanedPrecondition,
  cleanedSteps,
  qualityScore,
  cleanStatus,
}: CleanCompareProps) {
  const [showOriginal, setShowOriginal] = useState(false);

  if (!originalRaw) return null;

  return (
    <div className="mt-3 border border-sy-border rounded-lg overflow-hidden">
      <div className="flex items-center justify-between px-3 py-2 bg-sy-bg-2">
        <div className="flex items-center gap-2">
          <span className="text-[11px] text-sy-text-3">清洗质量</span>
          {qualityScore !== null && (
            <span className="font-mono text-[12px] text-sy-accent font-semibold">
              {qualityScore.toFixed(1)}
            </span>
          )}
          {cleanStatus && (
            <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-mono ${STATUS_COLORS[cleanStatus] ?? ''}`}>
              {cleanStatus}
            </span>
          )}
        </div>
        <button
          type="button"
          onClick={() => setShowOriginal(!showOriginal)}
          className="text-[11px] text-sy-text-3 hover:text-sy-text-2 transition-colors"
        >
          {showOriginal ? '隐藏原文' : '查看原文'}
        </button>
      </div>

      {showOriginal && (
        <div className="grid grid-cols-2 divide-x divide-sy-border">
          <div className="p-3">
            <div className="text-[10px] text-sy-text-3 mb-1 font-mono">清洗前</div>
            <pre className="text-[11px] text-sy-text-2 whitespace-pre-wrap font-mono leading-relaxed">
              {JSON.stringify(originalRaw, null, 2)}
            </pre>
          </div>
          <div className="p-3">
            <div className="text-[10px] text-sy-accent mb-1 font-mono">清洗后</div>
            <div className="text-[12px] text-sy-text font-medium mb-1">{cleanedTitle}</div>
            <div className="text-[11px] text-sy-text-3 mb-2">{cleanedPrecondition}</div>
            {cleanedSteps.map((step, i) => (
              <div key={`step-${i}`} className="flex gap-2 text-[11px] mb-1">
                <span className="font-mono text-sy-text-3 shrink-0">{i + 1}.</span>
                <div>
                  <p className="text-sy-text-2">{step.action}</p>
                  <p className="text-sy-accent/80 text-[10px]">→ {step.expected_result}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
```

**Step 3: Type check**

```bash
cd frontend && bunx tsc --noEmit
```

**Step 4: Commit**

```bash
git add frontend/src/app/(main)/testcases/_components/CleanCompare.tsx
git commit -m "feat(testcases): add clean comparison view for imported cases

Shows quality score, clean status badge, and expandable before/after
comparison with original raw data vs cleaned structured content.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

## Phase 4: AI 模型配置增强 (P1)

### Task 10: 后端 — API Key 加密存储

**Files:**
- Create: `backend/app/core/encryption.py`
- Test: `tests/unit/test_core/test_encryption.py`

**Step 1: Write the failing test**

```python
# tests/unit/test_core/test_encryption.py
from app.core.encryption import encrypt_value, decrypt_value, mask_api_key


def test_encrypt_decrypt_roundtrip():
    original = "sk-1234567890abcdef"
    encrypted = encrypt_value(original)
    assert encrypted != original
    assert decrypt_value(encrypted) == original


def test_mask_api_key():
    assert mask_api_key("sk-1234567890abcdef1234567890abcdef") == "sk-1234****cdef"
    assert mask_api_key("short") == "****"
    assert mask_api_key("") == ""
```

**Step 2: Run test → FAIL**

**Step 3: Implement encryption.py**

```python
# backend/app/core/encryption.py
"""Symmetric encryption utilities for API key storage."""

import os

from cryptography.fernet import Fernet

_KEY = os.environ.get("ENCRYPTION_KEY", Fernet.generate_key().decode())
_fernet = Fernet(_KEY.encode() if isinstance(_KEY, str) else _KEY)


def encrypt_value(plaintext: str) -> str:
    return _fernet.encrypt(plaintext.encode()).decode()


def decrypt_value(ciphertext: str) -> str:
    return _fernet.decrypt(ciphertext.encode()).decode()


def mask_api_key(key: str) -> str:
    if not key:
        return ""
    if len(key) <= 8:
        return "****"
    return f"{key[:4]}****{key[-4:]}"
```

**Step 4: Run test → PASS**

```bash
cd backend && uv run pytest tests/unit/test_core/test_encryption.py -v
```

**Step 5: Commit**

```bash
git add backend/app/core/encryption.py tests/unit/test_core/test_encryption.py
git commit -m "feat(core): add Fernet encryption utility for API key storage

Provides encrypt/decrypt roundtrip and API key masking for display.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 11: 后端 — AiConfiguration 模型扩展 + 连接测试端点

**Files:**
- Modify: `backend/app/modules/ai_config/models.py`
- Modify: `backend/app/modules/ai_config/router.py`
- Modify: `backend/app/modules/ai_config/service.py`
- Create: Alembic migration

**Step 1: Add fields to model**

```python
# Add to AiConfiguration in models.py:
api_keys: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
vector_config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
```

**Step 2: Generate migration**

```bash
cd backend && uv run alembic revision --autogenerate -m "add api_keys and vector_config to ai_configurations"
```

**Step 3: Add connection test endpoints to router**

```python
# Add to backend/app/modules/ai_config/router.py

class TestLLMRequest(BaseModel):
    provider: str  # "zhipu" | "dashscope" | "openai"
    api_key: str
    model: str
    base_url: str | None = None

class TestEmbeddingRequest(BaseModel):
    provider: str
    api_key: str
    model: str

@router.post("/ai-config/test-llm")
async def test_llm_connection(data: TestLLMRequest):
    """Send a test message to validate LLM connectivity."""
    import time
    from app.ai.llm_client import invoke_llm
    start = time.time()
    try:
        result = await invoke_llm(
            messages=[{"role": "user", "content": "你好，请用一句话介绍自己。"}],
            provider=data.provider,
            max_retries=1,
        )
        elapsed = round(time.time() - start, 2)
        return {"success": True, "response": result.content[:200], "elapsed_seconds": elapsed}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.post("/ai-config/test-embedding")
async def test_embedding_connection(data: TestEmbeddingRequest):
    """Vectorize a test string to validate embedding connectivity."""
    import time
    from app.engine.rag.embedder import embed_texts
    start = time.time()
    try:
        vectors = await embed_texts(["这是一条测试文本，用于验证向量化连接。"])
        elapsed = round(time.time() - start, 2)
        dimension = len(vectors[0]) if vectors else 0
        return {"success": True, "dimension": dimension, "elapsed_seconds": elapsed}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

**Step 4: Commit**

```bash
git add backend/app/modules/ai_config/ backend/alembic/versions/
git commit -m "feat(ai_config): add api_keys, vector_config fields and connection test endpoints

Extends AiConfiguration model. Adds POST /ai-config/test-llm and
POST /ai-config/test-embedding endpoints for connectivity validation.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 12: 前端 — AI 配置页面增强

**Files:**
- Modify: `frontend/src/app/(main)/settings/_components/AIModelSettings.tsx`
- Create: `frontend/src/app/(main)/settings/_components/ParamTooltip.tsx`
- Create: `frontend/src/app/(main)/settings/_components/ConnectionTestButton.tsx`
- Create: `frontend/src/app/(main)/settings/_components/VectorModelSettings.tsx`

**Step 1: Create ParamTooltip component**

```tsx
// frontend/src/app/(main)/settings/_components/ParamTooltip.tsx
'use client';

import { HelpCircle } from 'lucide-react';
import { useState } from 'react';

const TOOLTIPS: Record<string, { label: string; desc: string; recommend: string }> = {
  temperature: {
    label: '温度（Temperature）',
    desc: '控制输出的随机性。值越高，回复越多样化和创意；值越低，回复越确定和保守。',
    recommend: '推荐值：0.2（用例生成）/ 0.7（探索模式）',
  },
  top_p: {
    label: '核采样（Top-P）',
    desc: '控制候选词的概率范围。值越小，模型越倾向于选择高概率的词；值越大，输出越多样。',
    recommend: '推荐值：0.9（平衡模式）',
  },
  max_tokens: {
    label: '最大 Token 数（Max Tokens）',
    desc: '限制单次回复的最大长度。用例生成建议较大值以避免截断。',
    recommend: '推荐值：4096（用例生成）/ 2048（对话）',
  },
  frequency_penalty: {
    label: '频率惩罚（Frequency Penalty）',
    desc: '降低模型重复相同内容的倾向。正值减少重复，负值增加重复。',
    recommend: '推荐值：0.3',
  },
  presence_penalty: {
    label: '存在惩罚（Presence Penalty）',
    desc: '鼓励模型讨论新话题。正值增加话题多样性。',
    recommend: '推荐值：0.1',
  },
};

export function ParamTooltip({ param }: { param: string }) {
  const [show, setShow] = useState(false);
  const tip = TOOLTIPS[param];
  if (!tip) return null;

  return (
    <span className="relative inline-block ml-1">
      <HelpCircle
        className="w-3.5 h-3.5 text-sy-text-3 hover:text-sy-accent cursor-help transition-colors"
        onMouseEnter={() => setShow(true)}
        onMouseLeave={() => setShow(false)}
      />
      {show && (
        <div className="absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-2 w-64 p-3 rounded-lg bg-sy-bg-1 border border-sy-border shadow-lg text-[11px]">
          <div className="font-semibold text-sy-text mb-1">{tip.label}</div>
          <div className="text-sy-text-2 leading-relaxed mb-1.5">{tip.desc}</div>
          <div className="text-sy-accent text-[10px] font-mono">{tip.recommend}</div>
          <div className="absolute top-full left-1/2 -translate-x-1/2 w-2 h-2 bg-sy-bg-1 border-r border-b border-sy-border rotate-45 -mt-1" />
        </div>
      )}
    </span>
  );
}
```

**Step 2: Create ConnectionTestButton component**

```tsx
// frontend/src/app/(main)/settings/_components/ConnectionTestButton.tsx
'use client';

import { CheckCircle, Loader2, XCircle, Zap } from 'lucide-react';
import { useState } from 'react';

interface ConnectionTestButtonProps {
  testEndpoint: string;
  payload: Record<string, unknown>;
  label?: string;
}

export function ConnectionTestButton({ testEndpoint, payload, label = '测试连接' }: ConnectionTestButtonProps) {
  const [state, setState] = useState<'idle' | 'testing' | 'success' | 'error'>('idle');
  const [result, setResult] = useState<{ response?: string; elapsed?: number; error?: string; dimension?: number } | null>(null);

  const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api';

  const handleTest = async () => {
    setState('testing');
    setResult(null);
    try {
      const res = await fetch(`${API_BASE}${testEndpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (data.success) {
        setState('success');
        setResult(data);
      } else {
        setState('error');
        setResult({ error: data.error });
      }
    } catch (e) {
      setState('error');
      setResult({ error: e instanceof Error ? e.message : '连接失败' });
    }
  };

  return (
    <div>
      <button
        type="button"
        onClick={handleTest}
        disabled={state === 'testing'}
        className="flex items-center gap-1.5 px-3 py-1.5 text-[11px] font-medium rounded-md border border-sy-border hover:border-sy-accent/40 hover:text-sy-accent transition-all disabled:opacity-50"
      >
        {state === 'testing' ? (
          <Loader2 className="w-3.5 h-3.5 animate-spin" />
        ) : (
          <Zap className="w-3.5 h-3.5" />
        )}
        {state === 'testing' ? '测试中...' : label}
      </button>
      {result && (
        <div className={`mt-2 p-2 rounded-md text-[11px] ${state === 'success' ? 'bg-sy-accent/10 border border-sy-accent/30' : 'bg-sy-danger/10 border border-sy-danger/30'}`}>
          {state === 'success' ? (
            <div className="flex items-start gap-1.5">
              <CheckCircle className="w-3.5 h-3.5 text-sy-accent shrink-0 mt-0.5" />
              <div>
                <div className="text-sy-accent font-medium">连接成功</div>
                {result.elapsed && <div className="text-sy-text-3 mt-0.5">耗时 {result.elapsed}s</div>}
                {result.response && <div className="text-sy-text-2 mt-1 truncate">{result.response}</div>}
                {result.dimension && <div className="text-sy-text-3 mt-0.5">向量维度：{result.dimension}</div>}
              </div>
            </div>
          ) : (
            <div className="flex items-start gap-1.5">
              <XCircle className="w-3.5 h-3.5 text-sy-danger shrink-0 mt-0.5" />
              <div>
                <div className="text-sy-danger font-medium">连接失败</div>
                <div className="text-sy-text-3 mt-0.5">{result.error}</div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
```

**Step 3: Create VectorModelSettings component**

```tsx
// frontend/src/app/(main)/settings/_components/VectorModelSettings.tsx
'use client';

import { Database } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import { ConnectionTestButton } from './ConnectionTestButton';

const KNOWN_DIMENSIONS: Record<string, number> = {
  'embedding-3': 2048,
  'text-embedding-v3': 1024,
  'text-embedding-3-small': 1536,
  'text-embedding-3-large': 3072,
};

interface VectorModelSettingsProps {
  config: { provider?: string; model?: string; dimension?: number } | null;
  onSave: (config: { provider: string; model: string; dimension: number }) => void;
}

export function VectorModelSettings({ config, onSave }: VectorModelSettingsProps) {
  const [provider, setProvider] = useState(config?.provider ?? 'zhipu');
  const [model, setModel] = useState(config?.model ?? 'embedding-3');
  const [dimension, setDimension] = useState(config?.dimension ?? 2048);

  useEffect(() => {
    const known = KNOWN_DIMENSIONS[model];
    if (known) setDimension(known);
  }, [model]);

  const handleSave = useCallback(() => {
    onSave({ provider, model, dimension });
  }, [provider, model, dimension, onSave]);

  return (
    <div className="border border-sy-border rounded-lg p-4 mt-4">
      <div className="flex items-center gap-2 mb-4">
        <Database className="w-4 h-4 text-sy-purple" />
        <h4 className="text-[13px] font-semibold text-sy-text">向量模型配置</h4>
      </div>

      <div className="space-y-3">
        <div>
          <label className="text-[11px] text-sy-text-3 block mb-1">向量模型提供商</label>
          <select
            value={provider}
            onChange={(e) => setProvider(e.target.value)}
            className="w-full px-3 py-1.5 text-[12px] bg-sy-bg-2 border border-sy-border rounded-md text-sy-text"
          >
            <option value="zhipu">智谱 AI</option>
            <option value="dashscope">阿里百炼</option>
            <option value="openai">OpenAI</option>
          </select>
        </div>

        <div>
          <label className="text-[11px] text-sy-text-3 block mb-1">模型名称</label>
          <input
            type="text"
            value={model}
            onChange={(e) => setModel(e.target.value)}
            className="w-full px-3 py-1.5 text-[12px] bg-sy-bg-2 border border-sy-border rounded-md text-sy-text"
            placeholder="如 embedding-3 / text-embedding-v3"
          />
        </div>

        <div>
          <label className="text-[11px] text-sy-text-3 block mb-1">
            向量维度
            {KNOWN_DIMENSIONS[model] && (
              <span className="text-sy-accent ml-1">(已自动填充)</span>
            )}
          </label>
          <input
            type="number"
            value={dimension}
            onChange={(e) => setDimension(Number(e.target.value))}
            className="w-full px-3 py-1.5 text-[12px] bg-sy-bg-2 border border-sy-border rounded-md text-sy-text font-mono"
          />
        </div>

        <div className="flex items-center gap-3 pt-2">
          <ConnectionTestButton
            testEndpoint="/ai-config/test-embedding"
            payload={{ provider, model, api_key: '' }}
            label="测试向量化"
          />
          <button
            type="button"
            onClick={handleSave}
            className="px-3 py-1.5 text-[11px] font-medium rounded-md bg-sy-accent text-sy-bg hover:bg-sy-accent-2 transition-colors"
          >
            保存配置
          </button>
        </div>
      </div>
    </div>
  );
}
```

**Step 4: Type check**

```bash
cd frontend && bunx tsc --noEmit
```

**Step 5: Commit**

```bash
git add frontend/src/app/(main)/settings/_components/
git commit -m "feat(settings): add ParamTooltip, ConnectionTestButton, VectorModelSettings

ParamTooltip provides hover explanations for LLM parameters.
ConnectionTestButton validates LLM/embedding connectivity.
VectorModelSettings configures vector model with auto-dimension fill.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 13: 前端 — AIModelSettings 增加 API Key 输入和 Tooltip

**Files:**
- Modify: `frontend/src/app/(main)/settings/_components/AIModelSettings.tsx`

**Step 1: 在现有组件中集成**

对 AIModelSettings.tsx 进行以下修改：
1. 引入 `ParamTooltip` 和 `ConnectionTestButton`
2. 为每个参数名旁边添加 `<ParamTooltip param="xxx" />`
3. 添加 API Key 输入区域（支持各提供商独立 key）
4. 添加连接测试按钮

关键修改点：
- 在每个参数 label 后追加 `<ParamTooltip param="temperature" />` 等
- 新增 API Key 区域，带密码输入框和脱敏显示
- 新增 `ConnectionTestButton` 组件引用

**Step 2: Type check + lint**

```bash
cd frontend && bunx tsc --noEmit && bunx biome check .
```

**Step 3: Commit**

```bash
git add frontend/src/app/(main)/settings/_components/AIModelSettings.tsx
git commit -m "feat(settings): integrate API key input, param tooltips and connection test

AIModelSettings now includes per-provider API key input with masking,
parameter hover tooltips, and LLM connection test button.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

## Phase 5: 端到端验证

### Task 14: 后端 lint + type check

**Step 1:**
```bash
cd backend && uv run ruff check . && uv run ruff format --check .
```

**Step 2:**
```bash
cd backend && uv run pytest -v --tb=short
```

### Task 15: 前端 lint + type check + build

**Step 1:**
```bash
cd frontend && bunx biome check . && bunx tsc --noEmit
```

**Step 2:**
```bash
cd frontend && bun run build
```

### Task 16: 更新 progress.json 状态

将已完成的 TASK 标记为 `done`，更新 `stats`。

---

## 依赖关系图

```
Task 1 (backend messages+cases)
  └→ Task 2 (frontend verify CaseCard)

Task 3 (progress.json) — 独立

Task 4 (DB migration)
  └→ Task 5 (cleaner engine)
  └→ Task 6 (batch parser)
       └→ Task 7 (Celery task)
            └→ Task 8 (Qdrant vectorize)
            └→ Task 9 (frontend clean compare)

Task 10 (encryption)
  └→ Task 11 (ai_config endpoints)
       └→ Task 12 (frontend components)
            └→ Task 13 (integrate into AIModelSettings)

Task 14-16 (validation) — 最后
```
