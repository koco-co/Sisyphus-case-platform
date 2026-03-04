# Agent 系统实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 实现双 Agent 系统（生成 Agent + 评审 Agent），确保测试用例质量

**Architecture:**
- 生成 Agent：负责生成测试用例
- 评审 Agent：负责评审用例质量、规范、格式
- 编排器：协调两个 Agent 的交互
- 迭代优化：评审不通过则重新生成

**Tech Stack:** FastAPI, WebSocket, LLM Providers, Vector Retriever

---

## Task 1: 创建 Agent 基类

**Files:**
- Create: `backend/app/agents/base.py`
- Create: `backend/app/agents/__init__.py`

**Step 1: Write failing test for Agent base class**

创建 `backend/app/tests/test_agent_base.py`:

```python
import pytest
from app.agents.base import Agent, AgentResponse

@pytest.mark.asyncio
async def test_agent_interface():
    """测试 Agent 接口"""
    # 这会失败，因为 Agent 是抽象类
    agent = Agent()
    result = await agent.run("test input")
    assert result.success is True
```

**Step 2: Run test to verify it fails**

```bash
cd backend
uv run pytest app/tests/test_agent_base.py::test_agent_interface -v
```

Expected: FAIL with "Cannot instantiate abstract class"

**Step 3: Implement Agent base class**

创建 `backend/app/agents/base.py`:

```python
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from pydantic import BaseModel

class AgentResponse(BaseModel):
    """Agent 响应模型"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    metadata: Optional[Dict] = None

class Agent(ABC):
    """Agent 抽象基类"""

    def __init__(self, llm_provider, name: str = "Agent"):
        """
        初始化 Agent

        Args:
            llm_provider: LLM 提供商实例
            name: Agent 名称
        """
        self.llm = llm_provider
        self.name = name

    @abstractmethod
    async def run(self, input_data: Any) -> AgentResponse:
        """
        执行 Agent 任务

        Args:
            input_data: 输入数据

        Returns:
            AgentResponse
        """
        pass

    @abstractmethod
    async def validate_output(self, output: Any) -> bool:
        """
        验证输出是否符合要求

        Args:
            output: 输出数据

        Returns:
            是否验证通过
        """
        pass
```

创建 `backend/app/agents/__init__.py`:

```python
from app.agents.base import Agent, AgentResponse
```

**Step 4: Update test**

修改 `backend/app/tests/test_agent_base.py`:

```python
import pytest
from app.agents.base import Agent, AgentResponse

def test_agent_response_model():
    """测试 Agent 响应模型"""
    response = AgentResponse(
        success=True,
        data={"test": "value"},
        metadata={"attempt": 1}
    )
    assert response.success is True
    assert response.data["test"] == "value"
```

**Step 5: Run tests**

```bash
uv run pytest app/tests/test_agent_base.py -v
```

Expected: PASS

**Step 6: Commit**

```bash
git add backend/app/agents/
git commit -m "feat: 创建 Agent 抽象基类"
```

---

## Task 2: 实现生成 Agent

**Files:**
- Create: `backend/app/agents/generator.py`

**Step 1: Write failing test for Generator Agent**

创建 `backend/app/tests/test_generator_agent.py`:

```python
import pytest
import os
from app.agents.generator import GeneratorAgent
from app.llm.factory import create_llm_provider

@pytest.mark.asyncio
async def test_generator_agent():
    """测试生成 Agent"""
    api_key = os.getenv("GLM_API_KEY")
    if not api_key:
        pytest.skip("需要 GLM_API_KEY 环境变量")

    llm = create_llm_provider("glm", api_key=api_key)
    agent = GeneratorAgent(llm)

    result = await agent.run({
        "requirement": "用户登录功能：输入用户名和密码登录系统",
        "test_points": ["验证正常登录", "验证密码错误"],
        "examples": []
    })

    assert result.success is True
    assert "test_cases" in result.data
    assert len(result.data["test_cases"]) > 0
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest app/tests/test_generator_agent.py::test_generator_agent -v
```

Expected: FAIL with "module 'app.agents.generator' not found"

**Step 3: Implement Generator Agent**

创建 `backend/app/agents/generator.py`:

```python
from typing import List, Dict, Any, Optional
from app.agents.base import Agent, AgentResponse
from app.rag.prompt_builder import PromptBuilder
import re
import json

class GeneratorAgent(Agent):
    """测试用例生成 Agent"""

    def __init__(self, llm_provider, prompt_builder: Optional[PromptBuilder] = None):
        super().__init__(llm_provider, name="GeneratorAgent")
        self.prompt_builder = prompt_builder or PromptBuilder()

    async def run(self, input_data: Dict[str, Any]) -> AgentResponse:
        """
        生成测试用例

        Args:
            input_data: 包含 requirement, test_points, examples

        Returns:
            AgentResponse，包含生成的测试用例
        """
        try:
            # 构建 Prompt
            prompt = await self.prompt_builder.build_generation_prompt(
                requirement=input_data["requirement"],
                test_points=input_data.get("test_points", []),
                examples=input_data.get("examples", [])
            )

            # 调用 LLM 生成
            response = await self.llm.generate(prompt)

            # 解析生成的用例
            test_cases = await self._parse_test_cases(response.text)

            return AgentResponse(
                success=True,
                data={"test_cases": test_cases},
                metadata={
                    "model": response.model,
                    "usage": response.usage
                }
            )

        except Exception as e:
            return AgentResponse(
                success=False,
                error=str(e)
            )

    async def _parse_test_cases(self, text: str) -> List[Dict[str, Any]]:
        """
        解析 LLM 输出的测试用例

        Args:
            text: LLM 生成的文本

        Returns:
            测试用例列表
        """
        # 尝试解析 CSV 格式
        lines = text.strip().split('\n')
        test_cases = []

        # 找到 CSV 表头
        header_index = -1
        for i, line in enumerate(lines):
            if '所属模块' in line or '用例标题' in line:
                header_index = i
                break

        if header_index == -1:
            # 没有找到表头，尝试按行解析
            return await self._parse_text_to_cases(text)

        # 解析 CSV 行
        for line in lines[header_index + 1:]:
            if not line.strip() or line.startswith('-') or line.startswith('='):
                continue

            # 简单的 CSV 解析（处理逗号分隔）
            parts = self._split_csv_line(line)
            if len(parts) >= 5:  # 至少包含：模块、标题、前置条件、步骤、预期
                test_cases.append({
                    "module": parts[0].strip('"'),
                    "title": parts[1].strip('"'),
                    "prerequisites": parts[2].strip('"') if len(parts) > 2 else "",
                    "steps": parts[3].strip('"') if len(parts) > 3 else "",
                    "expected_results": parts[4].strip('"') if len(parts) > 4 else "",
                    "keywords": parts[5].strip('"') if len(parts) > 5 else "",
                    "priority": parts[6].strip('"') if len(parts) > 6 else "2",
                    "case_type": parts[7].strip('"') if len(parts) > 7 else "功能测试",
                    "stage": parts[8].strip('"') if len(parts) > 8 else "功能测试阶段"
                })

        return test_cases

    async def _parse_text_to_cases(self, text: str) -> List[Dict[str, Any]]:
        """
        从纯文本解析测试用例（备用方案）

        Args:
            text: 纯文本

        Returns:
            测试用例列表
        """
        # 简单实现：提取"用例 X:"格式的用例
        cases = []
        case_pattern = r'用例\s*\d+[:：]\s*(.+?)(?=用例\s*\d+[:：]|$)'

        matches = re.findall(case_pattern, text, re.DOTALL)
        for match in matches:
            # 尝试提取字段
            title = self._extract_field(match, ['标题', '用例名称'])
            steps = self._extract_field(match, ['步骤', '操作步骤'])
            expected = self._extract_field(match, ['预期', '期望结果', '预期结果'])

            if title and steps:
                cases.append({
                    "title": title,
                    "steps": steps,
                    "expected_results": expected or "待补充",
                    "module": "通用",
                    "prerequisites": "",
                    "priority": "2"
                })

        return cases

    def _extract_field(self, text: str, keywords: List[str]) -> Optional[str]:
        """从文本中提取字段值"""
        for keyword in keywords:
            pattern = f'{keyword}[:：](.+?)(?=\n|\\n|$)'
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        return None

    def _split_csv_line(self, line: str) -> List[str]:
        """分割 CSV 行（处理引号内的逗号）"""
        parts = []
        current = []
        in_quotes = False

        for char in line:
            if char == '"':
                in_quotes = not in_quotes
            elif char == ',' and not in_quotes:
                parts.append(''.join(current))
                current = []
            else:
                current.append(char)

        if current:
            parts.append(''.join(current))

        return parts

    async def validate_output(self, output: List[Dict]) -> bool:
        """验证输出是否包含有效的测试用例"""
        if not output:
            return False

        for case in output:
            if not case.get("title") or not case.get("steps"):
                return False

        return True
```

**Step 4: Run tests (需要 API Key)**

```bash
export GLM_API_KEY=your-api-key
uv run pytest app/tests/test_generator_agent.py::test_generator_agent -v -s
```

Expected: PASS (如果有有效的 API key)

**Step 5: Commit**

```bash
git add backend/app/agents/generator.py backend/app/tests/test_generator_agent.py
git commit -m "feat: 实现生成 Agent"
```

---

## Task 3: 实现评审 Agent

**Files:**
- Create: `backend/app/agents/reviewer.py`

**Step 1: Write failing test for Reviewer Agent**

创建 `backend/app/tests/test_reviewer_agent.py`:

```python
import pytest
import os
from app.agents.reviewer import ReviewerAgent
from app.llm.factory import create_llm_provider

@pytest.mark.asyncio
async def test_reviewer_agent():
    """测试评审 Agent"""
    api_key = os.getenv("GLM_API_KEY")
    if not api_key:
        pytest.skip("需要 GLM_API_KEY 环境变量")

    llm = create_llm_provider("glm", api_key=api_key)
    agent = ReviewerAgent(llm)

    test_cases = [
        {
            "title": "用户登录测试",
            "steps": "1. 打开登录页面\n2. 输入用户名密码",
            "expected_results": "登录成功"
        }
    ]

    result = await agent.run({"test_cases": test_cases})

    assert result.success is True
    assert "passed" in result.data
    assert "feedback" in result.data
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest app/tests/test_reviewer_agent.py::test_reviewer_agent -v
```

Expected: FAIL with "module 'app.agents.reviewer' not found"

**Step 3: Implement Reviewer Agent**

创建 `backend/app/agents/reviewer.py`:

```python
from typing import List, Dict, Any
from app.agents.base import Agent, AgentResponse
from app.rag.prompt_builder import PromptBuilder
import re

class ReviewerAgent(Agent):
    """测试用例评审 Agent"""

    def __init__(self, llm_provider, prompt_builder: Optional[PromptBuilder] = None):
        super().__init__(llm_provider, name="ReviewerAgent")
        self.prompt_builder = prompt_builder or PromptBuilder()

    async def run(self, input_data: Dict[str, Any]) -> AgentResponse:
        """
        评审测试用例

        Args:
            input_data: 包含 test_cases 列表

        Returns:
            AgentResponse，包含评审结果
        """
        try:
            # 构建评审 Prompt
            prompt = await self.prompt_builder.build_review_prompt(
                input_data["test_cases"]
            )

            # 调用 LLM 评审
            response = await self.llm.generate(prompt)

            # 解析评审结果
            review_result = await self._parse_review_result(response.text)

            return AgentResponse(
                success=True,
                data=review_result,
                metadata={
                    "model": response.model,
                    "usage": response.usage
                }
            )

        except Exception as e:
            return AgentResponse(
                success=False,
                error=str(e)
            )

    async def _parse_review_result(self, text: str) -> Dict[str, Any]:
        """
        解析评审结果

        Args:
            text: LLM 输出的评审文本

        Returns:
            评审结果字典
        """
        # 提取总体评价
        passed = False
        if "通过" in text or "PASS" in text.upper():
            passed = True

        # 提取问题列表
        issues = []
        issue_pattern = r'(?:用例\s*(\d+)[：:]?\s*)?(.+?)(?=问题|改进建议|$)'
        matches = re.findall(issue_pattern, text, re.DOTALL)

        for case_num, issue in matches:
            if "步骤" in issue or "数据" in issue or "预期" in issue:
                issues.append({
                    "case_number": int(case_num) if case_num else None,
                    "issue": issue.strip()
                })

        # 提取改进建议
        suggestions = []
        if "改进建议" in text:
            suggestion_section = text.split("改进建议")[-1]
            suggestions = [
                line.strip()
                for line in suggestion_section.split('\n')
                if line.strip() and not line.startswith('-') and not line.startswith('=')
            ]

        return {
            "passed": passed,
            "issues": issues,
            "suggestions": suggestions,
            "raw_review": text
        }

    async def validate_output(self, output: Dict) -> bool:
        """验证评审结果是否有效"""
        return "passed" in output and isinstance(output["passed"], bool)
```

**Step 4: Run tests**

```bash
export GLM_API_KEY=your-api-key
uv run pytest app/tests/test_reviewer_agent.py::test_reviewer_agent -v -s
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/agents/reviewer.py backend/app/tests/test_reviewer_agent.py
git commit -m "feat: 实现评审 Agent"
```

---

## Task 4: 实现 Agent 编排器

**Files:**
- Create: `backend/app/agents/orchestrator.py`

**Step 1: Write failing test for Orchestrator**

创建 `backend/app/tests/test_orchestrator.py`:

```python
import pytest
import os
from app.agents.orchestrator import AgentOrchestrator
from app.llm.factory import create_llm_provider

@pytest.mark.asyncio
async def test_orchestrator_workflow():
    """测试编排器工作流"""
    api_key = os.getenv("GLM_API_KEY")
    if not api_key:
        pytest.skip("需要 GLM_API_KEY 环境变量")

    llm = create_llm_provider("glm", api_key=api_key)

    orchestrator = AgentOrchestrator(
        generator_llm=llm,
        reviewer_llm=llm,
        max_retries=2
    )

    result = await orchestrator.generate_with_review({
        "requirement": "用户登录功能",
        "test_points": ["验证正常登录"],
        "examples": []
    })

    assert result["success"] is True
    assert "test_cases" in result
    assert result.get("review_passed") is True
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest app/tests/test_orchestrator.py::test_orchestrator_workflow -v
```

Expected: FAIL with "module 'app.agents.orchestrator' not found"

**Step 3: Implement Orchestrator**

创建 `backend/app/agents/orchestrator.py`:

```python
from typing import List, Dict, Any, Optional
from app.agents.generator import GeneratorAgent
from app.agents.reviewer import ReviewerAgent
from app.rag.prompt_builder import PromptBuilder

class AgentOrchestrator:
    """Agent 编排器"""

    def __init__(
        self,
        generator_llm,
        reviewer_llm,
        max_retries: int = 3,
        prompt_builder: Optional[PromptBuilder] = None
    ):
        """
        初始化编排器

        Args:
            generator_llm: 生成 Agent 使用的 LLM
            reviewer_llm: 评审 Agent 使用的 LLM
            max_retries: 最大重试次数
            prompt_builder: Prompt 构建器
        """
        self.generator = GeneratorAgent(generator_llm, prompt_builder)
        self.reviewer = ReviewerAgent(reviewer_llm, prompt_builder)
        self.max_retries = max_retries

    async def generate_with_review(
        self,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        生成测试用例并评审（自动迭代优化）

        Args:
            input_data: 包含 requirement, test_points, examples

        Returns:
            生成和评审结果
        """
        last_feedback = None

        for attempt in range(self.max_retries):
            # 1. 生成测试用例
            if attempt > 0 and last_feedback:
                # 使用反馈重新生成
                input_data["feedback"] = last_feedback

            generation_result = await self.generator.run(input_data)

            if not generation_result.success:
                return {
                    "success": False,
                    "error": f"生成失败: {generation_result.error}",
                    "attempt": attempt + 1
                }

            test_cases = generation_result.data["test_cases"]

            # 2. 评审测试用例
            review_result = await self.reviewer.run({
                "test_cases": test_cases
            })

            if not review_result.success:
                return {
                    "success": False,
                    "error": f"评审失败: {review_result.error}",
                    "test_cases": test_cases,
                    "attempt": attempt + 1
                }

            review_data = review_result.data

            # 3. 检查是否通过
            if review_data["passed"]:
                return {
                    "success": True,
                    "test_cases": test_cases,
                    "review_passed": True,
                    "attempts": attempt + 1,
                    "review": review_data
                }
            else:
                # 4. 不通过，收集反馈重试
                last_feedback = self._collect_feedback(review_data)

                if attempt < self.max_retries - 1:
                    # 还有重试机会
                    continue
                else:
                    # 达到最大重试次数，返回当前结果
                    return {
                        "success": True,
                        "test_cases": test_cases,
                        "review_passed": False,
                        "attempts": self.max_retries,
                        "review": review_data,
                        "warning": "达到最大重试次数，评审未通过"
                    }

    def _collect_feedback(self, review_data: Dict) -> str:
        """
        从评审结果中收集反馈

        Args:
            review_data: 评审数据

        Returns:
            反馈文本
        """
        feedback_parts = []

        if review_data.get("issues"):
            feedback_parts.append("发现以下问题：")
            for issue in review_data["issues"]:
                case_num = issue.get("case_number")
                case_info = f"用例 {case_num}: " if case_num else ""
                feedback_parts.append(f"- {case_info}{issue['issue']}")

        if review_data.get("suggestions"):
            feedback_parts.append("\n改进建议：")
            for suggestion in review_data["suggestions"]:
                feedback_parts.append(f"- {suggestion}")

        return "\n".join(feedback_parts)
```

**Step 4: Run tests**

```bash
export GLM_API_KEY=your-api-key
uv run pytest app/tests/test_orchestrator.py::test_orchestrator_workflow -v -s
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/agents/orchestrator.py backend/app/tests/test_orchestrator.py
git commit -m "feat: 实现 Agent 编排器"
```

---

## Task 5: 创建用例生成 API（WebSocket 流式输出）

**Files:**
- Create: `backend/app/api/generation.py`
- Modify: `backend/app/main.py`

**Step 1: Write test for generation API**

创建 `backend/app/tests/test_generation_api.py`:

```python
import pytest
import asyncio
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_generate_test_cases():
    """测试生成 API"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            "/api/generate/",
            json={
                "requirement": "用户登录功能",
                "test_points": ["验证正常登录"],
                "project_id": 1
            }
        )
        # 注意：实际使用时应该用 WebSocket
        # 这里只测试 API 端点存在
        assert response.status_code in [200, 401]  # 可能需要认证
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest app/tests/test_generation_api.py::test_generate_test_cases -v
```

Expected: FAIL with "404 Not Found"

**Step 3: Implement generation API**

创建 `backend/app/api/generation.py`:

```python
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any
from app.database import get_db
from app.models.project import Project
from app.models.user_config import UserConfig
from app.llm.factory import create_llm_provider
from app.agents.orchestrator import AgentOrchestrator
from app.rag.retriever import VectorRetriever
import json

router = APIRouter(prefix="/api/generate", tags=["generation"])

class ConnectionManager:
    """WebSocket 连接管理器"""

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_progress(self, websocket: WebSocket, message: Dict[str, Any]):
        await websocket.send_text(json.dumps(message, ensure_ascii=False))

manager = ConnectionManager()

@router.websocket("/ws")
async def generate_test_cases_websocket(websocket: WebSocket):
    """
    WebSocket 端点，用于流式生成测试用例

    客户端发送：
    {
        "requirement": "需求文档",
        "test_points": ["测试点1", "测试点2"],
        "project_id": 1,
        "use_rag": true
    }

    服务器发送进度：
    {
        "stage": "analyzing",  // analyzing, generating, reviewing, completed
        "message": "正在分析需求...",
        "progress": 30
    }

    服务器发送用例：
    {
        "stage": "completed",
        "test_cases": [...],
        "review_passed": true
    }
    """
    await manager.connect(websocket)

    try:
        # 接收初始消息
        data = await websocket.receive_text()
        request = json.loads(data)

        requirement = request.get("requirement")
        test_points = request.get("test_points", [])
        project_id = request.get("project_id")
        use_rag = request.get("use_rag", True)

        if not requirement:
            await manager.send_progress(websocket, {
                "stage": "error",
                "message": "缺少需求文档"
            })
            return

        # 获取激活的 LLM 配置
        async for db in get_db():
            result = await db.execute(
                select(UserConfig).where(UserConfig.is_active == True)
            )
            config = result.scalar_one_or_none()
            break

        if not config:
            await manager.send_progress(websocket, {
                "stage": "error",
                "message": "请先配置 LLM 提供商"
            })
            return

        # 创建 LLM 实例
        llm = create_llm_provider(
            config.provider,
            api_key=config.api_key_encrypted
        )

        # 向量检索历史用例
        examples = []
        if use_rag:
            await manager.send_progress(websocket, {
                "stage": "retrieving",
                "message": "正在检索相似的历史用例...",
                "progress": 10
            })

            retriever = VectorRetriever()
            similar_cases = await retriever.search_similar_cases(
                query=requirement,
                top_k=5,
                project_id=project_id
            )

            examples = [
                {
                    "module": case.module,
                    "title": case.title,
                    "prerequisites": case.prerequisites,
                    "steps": case.steps,
                    "expected_results": case.expected_results,
                    "priority": case.priority
                }
                for case in similar_cases
            ]

        # 创建编排器
        orchestrator = AgentOrchestrator(
            generator_llm=llm,
            reviewer_llm=llm,
            max_retries=3
        )

        # 开始生成
        await manager.send_progress(websocket, {
            "stage": "generating",
            "message": "正在生成测试用例...",
            "progress": 30
        })

        result = await orchestrator.generate_with_review({
            "requirement": requirement,
            "test_points": test_points,
            "examples": examples
        })

        if result["success"]:
            await manager.send_progress(websocket, {
                "stage": "reviewing",
                "message": "正在评审测试用例...",
                "progress": 70
            })

            # 发送最终结果
            await manager.send_progress(websocket, {
                "stage": "completed",
                "message": "生成完成！",
                "progress": 100,
                "test_cases": result["test_cases"],
                "review_passed": result.get("review_passed", False),
                "attempts": result.get("attempts", 1),
                "review": result.get("review", {})
            })
        else:
            await manager.send_progress(websocket, {
                "stage": "error",
                "message": result.get("error", "生成失败")
            })

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        await manager.send_progress(websocket, {
            "stage": "error",
            "message": f"错误: {str(e)}"
        })
        manager.disconnect(websocket)
```

修改 `backend/app/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api import projects, cases, config, vectors, generation

app = FastAPI(
    title="Sisyphus API",
    description="测试用例生成平台 API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router)
app.include_router(cases.router)
app.include_router(config.router)
app.include_router(vectors.router)
app.include_router(generation.router)

@app.get("/")
async def root():
    return {
        "message": "Sisyphus 测试用例生成平台 API",
        "version": "0.1.0",
        "status": "running"
    }
```

**Step 4: Run tests**

```bash
uv run pytest app/tests/test_generation_api.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/api/generation.py backend/app/main.py
git commit -m "feat: 实现用例生成 API（WebSocket 流式输出）"
```

---

## 完成检查清单

- [ ] Agent 基类实现完成
- [ ] 生成 Agent 可以生成测试用例
- [ ] 评审 Agent 可以评审用例质量
- [ ] 编排器可以协调两个 Agent
- [ ] WebSocket API 支持流式输出
- [ ] 所有测试通过

## 下一步

继续实施：
- `2026-03-04-05-document-parsers.md` - 文档解析插件
- `2026-03-05-01-frontend-foundation.md` - 前端基础架构
