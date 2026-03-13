# Claude Instructions — Sisyphus Case Platform

## Interaction Language

Always respond to me in Simplified Chinese (简体中文). This applies to code explanations, summaries, and general chat. However, keep the source code and technical identifiers (variable names, function names) in their original language.

## 项目概述

**Sisyphus-case-platform**（代号 Sisyphus-Y）是 AI 驱动的企业级功能测试用例自动生成平台，面向数据中台场景。

核心理念：显式拆分「测什么」（M04 测试点/场景地图）和「怎么测」（M05 用例步骤），通过评审节点前置拦截方向错误，构建 需求录入 → 需求分析 → 测试点确认 → 用例生成 → 执行回流 的完整测试生命周期。

## 技术栈

| 层级              | 技术                                                     | 版本     |
| ----------------- | -------------------------------------------------------- | -------- |
| 前端框架          | **Next.js App Router** + TypeScript                      | **16**   |
| 样式方案          | Tailwind CSS（扩展 `sy-*` 颜色 token）                   | v3       |
| 组件库            | shadcn/ui                                                | latest   |
| 图标库            | lucide-react（**禁止用 emoji 作 UI 元素**）              | latest   |
| 状态管理          | Zustand                                                  | latest   |
| 可视化            | React Flow（场景地图）/ Recharts（看板）                 | latest   |
| **后端框架**      | **FastAPI** + Python                                     | **3.12** |
| ORM               | SQLAlchemy 2.0（async，asyncpg 驱动）                    | 2.0      |
| AI 引擎           | LangChain + LangGraph                                    | latest   |
| 默认模型          | 智谱 GLM-4-Flash（诊断/追问）/ 阿里 Qwen-Max（用例生成） | —        |
| 向量库            | Qdrant                                                   | latest   |
| 关系数据库        | PostgreSQL                                               | 15       |
| 缓存/队列         | Redis                                                    | 7        |
| 异步任务          | Celery + Redis                                           | latest   |
| 文档解析          | python-docx / PyMuPDF / pypdf / PaddleOCR                | latest   |
| 对象存储          | MinIO                                                    | latest   |
| **Python 包管理** | **uv**（禁止 pip / conda / poetry）                      | latest   |
| **前端包管理**    | **bun**（禁止 npm / yarn / pnpm）                        | latest   |

---

## 项目目录结构

```
项目根/
├── CLAUDE.md
├── docs/
├── backend/
│   └── app/
│       ├── core/               # 基础设施（db, redis, minio, config）
│       ├── modules/            # 21 个业务模块（见模块对照表）
│       │   └── <name>/
│       │       ├── __init__.py
│       │       ├── router.py   # 只做参数校验，调用 service，禁止写 Prompt
│       │       ├── models.py   # SQLAlchemy ORM 模型
│       │       ├── schemas.py  # Pydantic 请求/响应模型
│       │       └── service.py  # 业务逻辑，接收 AsyncSession 参数
│       └── engine/             # AI 引擎（所有 Prompt 只能写在此层）
│           ├── uda/            # 文档解析（docx/pdf/md + 图片 OCR）
│           ├── diagnosis/      # 诊断引擎（扫描/追问/清单）
│           ├── scene_map/      # 场景地图生成
│           ├── case_gen/       # 用例生成（含 SSE 流式）
│           ├── diff/           # Myers Diff + LLM 语义分析
│           └── rag/            # 向量嵌入与检索
└── frontend/
    └── src/
        └── app/
            ├── (auth)/         # 登录等无鉴权页面
            └── (main)/         # 主业务页面（见模块对照表）
```

---

## 模块对照表

| 编号 | 后端 `modules/`  | 前端 `(main)/`                            | 职责                     |
| ---- | ---------------- | ----------------------------------------- | ------------------------ |
| M00  | `products/`      | `products/` `iterations/` `requirements/` | 子产品/迭代/需求三级管理 |
| M01  | `uda/`           | —                                         | 文档解析引擎，UDA 层     |
| M02  | `import_clean/`  | —                                         | 历史数据导入清洗         |
| M03  | `diagnosis/`     | `analysis/diagnosis/`                     | 需求分析（原健康诊断）   |
| M04  | `scene_map/`     | `analysis/scene-map/`                     | 测试点分析 & 场景地图    |
| M05  | `generation/`    | `workbench/`                              | 对话式用例生成工作台     |
| M06  | `testcases/`     | `testcases/`                              | 用例管理中心             |
| M07  | `diff/`          | `diff/`                                   | 需求 Diff & 变更影响     |
| M08  | `coverage/`      | `analysis/coverage/`                      | 需求覆盖度矩阵           |
| M09  | ~~`test_plan/`~~ | —                                         | ~~迭代测试计划（已裁剪）~~ |
| M10  | `templates/`     | —                                         | 用例模板库               |
| M11  | `knowledge/`     | `knowledge/`                              | 知识库管理（RAG）        |
| M12  | `export/`        | —                                         | 用例导出与集成           |
| M13  | `execution/`     | —                                         | 执行结果回流             |
| M14  | `analytics/`     | —（已合并至仪表盘）                       | 质量分析（合并至 M19）   |
| M16  | `notification/`  | —                                         | 通知系统                 |
| M17  | `search/`        | —                                         | 全局搜索                 |
| M18  | ~~`collaboration/`~~ | —                                    | ~~协作功能（已裁剪）~~   |
| M19  | `dashboard/`     | `(main)/`                                 | 首页仪表盘（含质量分析） |
| M20  | `audit/`         | —                                         | 操作审计日志             |
| M21  | `recycle/`       | —                                         | 回收站（软删除）         |

---

## 开发规范

### 代码质量工具

```bash
# Python（每次提交前必须全部通过）
uv run ruff check .            # lint
uv run ruff format .           # 格式化
uv run pyright app/            # 类型检查（standard 模式）

# 前端（每次提交前必须全部通过）
bunx biome check .             # lint + format 检查
bunx biome check --write .     # 自动修复
bunx tsc --noEmit              # 类型检查
```

### 命名约定

| 场景                  | 规范              | 示例                         |
| --------------------- | ----------------- | ---------------------------- |
| Python 文件/变量/函数 | `snake_case`      | `scene_map_service.py`       |
| Python 类             | `PascalCase`      | `SceneMapService`            |
| TypeScript 变量/函数  | `camelCase`       | `fetchTestCases`             |
| TypeScript 组件/类型  | `PascalCase`      | `CaseCard` / `TestCase`      |
| API 路由              | `kebab-case`      | `/api/scene-map/generate`    |
| 数据库表名            | `snake_case` 复数 | `test_cases` / `scene_nodes` |
| 数据库字段            | `snake_case`      | `created_at` / `req_id`      |

### 软删除（所有核心业务表）

通过 `SoftDeleteMixin` 实现，字段为 `deleted_at`（`DateTime | None`）。

```python
# 所有查询必须过滤，禁止直接查全表
.where(Model.deleted_at.is_(None))
```

### Git 规范

- 分支：`feat/<module>-<desc>` / `fix/<desc>` / `docs/<desc>` / `refactor/<desc>`
- Commit：Conventional Commits（`feat:` `fix:` `docs:` `refactor:` `test:` `chore:`）
- PR 合并前必须：① lint/type check 通过，② 更新 `CHANGELOG.md`

### 测试规范

- 框架：pytest + pytest-asyncio（`asyncio_mode = "auto"`）
- 路径：`tests/unit/test_<module>/test_<feature>.py`
- 公共 Fixture 放 `tests/conftest.py`，模块级 Fixture 放模块测试目录内

---

## 常用命令

```bash
# 一键启动开发环境
./init.sh

# ── 后端 ──────────────────────────────────────────────────────────────
cd backend
uv sync --all-extras                               # 安装所有依赖（含 extras）
uv run uvicorn app.main:app --reload --port 8000   # 启动开发服务器
uv run alembic upgrade head                        # 执行数据库迁移
uv run alembic revision --autogenerate -m "描述"   # 生成迁移文件
uv run pytest -v                                   # 运行测试
uv run pytest --cov=app                            # 测试 + 覆盖率报告

# ── 前端 ──────────────────────────────────────────────────────────────
cd frontend
bun install                                        # 安装依赖
bun dev                                            # 启动开发服务器（:3000）
bun run build                                      # 生产构建

# ── 基础设施（Docker）────────────────────────────────────────────────
docker compose -f docker/docker-compose.yml up -d     # 启动 PG/Redis/Qdrant/MinIO
docker compose -f docker/docker-compose.yml down
docker compose -f docker/docker-compose.yml logs -f
```

---

## UI 设计规范

### 设计 Token（Tailwind 扩展，`tailwind.config.ts` 中必须配置）

```ts
// 禁止在任何组件中硬编码色值，统一通过 class 引用
colors: {
  'sy-bg':       '#0d0f12',   // 最底层页面背景
  'sy-bg-1':     '#131619',   // 侧边栏/顶栏/一级卡片
  'sy-bg-2':     '#1a1e24',   // 输入框/hover/二级卡片
  'sy-bg-3':     '#212730',   // 标签/徽章/三级容器
  'sy-border':   '#2a313d',
  'sy-border-2': '#353d4a',
  'sy-text':     '#e2e8f0',   // 主文字
  'sy-text-2':   '#94a3b8',   // 次要文字
  'sy-text-3':   '#566577',   // 辅助文字/占位符
  'sy-accent':   '#00d9a3',   // 品牌色
  'sy-accent-2': '#00b386',   // 品牌色 hover
  'sy-warn':     '#f59e0b',
  'sy-danger':   '#f43f5e',
  'sy-info':     '#3b82f6',
  'sy-purple':   '#a855f7',
},
fontFamily: {
  sans:    ['DM Sans', 'sans-serif'],
  mono:    ['JetBrains Mono', 'monospace'],
  display: ['Syne', 'sans-serif'],
},
keyframes: {
  blink: { '0%,100%': { opacity: '1' }, '50%': { opacity: '0' } },
},
animation: { blink: 'blink 0.8s infinite' },
```

**硬编码报错示例**：`style={{ color: '#00d9a3' }}` / `className="text-[#00d9a3]"` → 改为 `className="text-sy-accent"`。

### 布局架构

- **全局框架**：顶部水平导航栏 `topbar`（高度 49px），9个菜单项：仪表盘/分析台/工作台/需求Diff/用例库/模板库/知识库/回收站/设置
- **三栏工作台**（生成工作台/诊断/测试点确认）：
  - `col-left`（固定宽）：需求导航 / 报告列表
  - `col-mid`（`flex-1`）：AI 主区域（对话 + 流式输出）
  - `col-right`（固定宽）：辅助信息（用例预览 / 场景地图）
  - 三栏各自独立 `overflow-y-auto`，高度 `calc(100vh - 49px - subNavHeight)`
- **原型文件**：`Sisyphus-Y.html`（项目根目录），是所有 UI 决策的唯一视觉标准

### 核心复用组件

| 组件             | 路径                                    | 规格                                                       |
| ---------------- | --------------------------------------- | ---------------------------------------------------------- |
| `StatusBadge`    | `components/ui/StatusBadge.tsx`         | `font-mono text-[11px] rounded-full px-2 py-0.5`，5 种变体 |
| `CaseCard`       | `components/workspace/CaseCard.tsx`     | steps 数组逐条渲染，**绝对禁止 JSON.stringify**            |
| `StreamCursor`   | `components/workspace/StreamCursor.tsx` | `w-0.5 h-3.5 bg-sy-warn animate-blink`                     |
| `ThreeColLayout` | `components/layout/ThreeColLayout.tsx`  | 三栏固定高布局，各列独立滚动                               |
| `FormDialog`     | `components/ui/FormDialog.tsx`              | 可复用模态表单对话框                                        |
| `FormField`      | `components/ui/FormField.tsx`               | 表单字段包装器（label + error）                             |
| `TableSkeleton`  | `components/ui/TableSkeleton.tsx`           | 表格骨架屏加载动画                                          |

### 场景节点颜色编码

| 状态                    | Tailwind class                                                                 |
| ----------------------- | ------------------------------------------------------------------------------ |
| 已覆盖（document）      | `bg-sy-accent/10 border border-sy-accent/35 text-sy-accent`                    |
| AI 补全（supplemented） | `bg-sy-warn/10 border border-sy-warn/35 text-sy-warn`                          |
| 缺失/高风险（missing）  | `bg-sy-danger/10 border-[1.5px] border-sy-danger text-sy-danger font-semibold` |
| 待确认（pending）       | `bg-sy-bg-3 border border-dashed border-sy-border-2 text-sy-text-3`            |

### 微交互要求

- SSE 流式输出：`StreamCursor` 动画 + 思考过程可折叠
- 按钮 Loading：`<Loader2 className="animate-spin" />` + 文字切换
- 卡片 hover：`hover:-translate-y-px hover:border-sy-border-2 transition-all`
- 毛玻璃（需要时）：`backdrop-blur-md`

---

## 数据持久化要求（关键约束）

**核心原则：所有 AI 生成结果必须持久化到 PostgreSQL，页面刷新后必须能完整恢复。**

| AI 生成内容      | 持久化目标表                                                         |
| ---------------- | -------------------------------------------------------------------- |
| 分析对话 AI 响应 | `DiagnosisChatMessage`（role=assistant）→ 自动解析 → `DiagnosisRisk` |
| 测试点草稿       | `GenerationMessage` → 自动解析 → `TestPoint`（关联 SceneMap）        |
| 用例生成流       | `GenerationMessage` → SSE 完成后 → 自动解析 → `TestCase`             |
| 所有 AI 交互     | 关联 `session_id`，支持历史回溯（最近 100 条）                       |

SSE 流完成后，后端必须自动将完整响应保存到数据库，前端不负责持久化。

---

## AI 引擎约束

### 模型分工

| 模型             | 场景                   | 原因                       |
| ---------------- | ---------------------- | -------------------------- |
| 智谱 GLM-4-Flash | 需求分析、苏格拉底追问 | 中文理解强，响应快         |
| 阿里 Qwen-Max    | 复杂用例 CoT 生成      | 推理能力强，结构化输出稳定 |

### 容错降级

1. 主模型失败 → 重试 2 次（指数退避：1s / 2s）
2. 重试失败 → 自动降级备用模型
3. 所有 LLM 调用设置 `trust_env=False`（绕过系统代理）

### JSON 安全提取（强制规范）

```python
# 禁止直接 json.loads(result.content)，必须安全提取
import re, json

content = result.content
match = re.search(r'\{.*\}', content, re.DOTALL)   # 对象
# 或
match = re.search(r'\[.*\]', content, re.DOTALL)   # 数组
if not match:
    raise ValueError(f"LLM 返回格式异常，无法提取 JSON: {content[:200]}")
data = json.loads(match.group())
```

### Prompt 层级规范

所有 Prompt 必须在 `engine/` 层实现，禁止在 `modules/` 层写任何 LLM 调用逻辑。
完整的 Prompt 体系（System Prompt / Rules / 用户可配置 Prompt）见 `docs/PROMPT_RULES.md`。

### 环境变量

```env
LLM_PROVIDER=zhipu
ZHIPU_API_KEY=<key>
DASHSCOPE_API_KEY=<key>
DASHSCOPE_MODEL=qwen-max
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/sisyphus_y
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
QDRANT_URL=http://localhost:6333
```

---

## 导航架构（v2.0）

9 个顶级菜单项，由顶部水平导航栏承载：

| 菜单项   | 路由            | 子Tab/说明                                       |
| -------- | --------------- | ------------------------------------------------ |
| 仪表盘   | `/`             | 项目概览 + 质量分析 双Tab                         |
| 分析台   | `/analysis`     | 需求列表 / AI分析 / 场景地图 / 覆盖追踪 四子Tab   |
| 工作台   | `/workbench`    | 确认测试点 + 生成用例                             |
| 需求Diff | `/diff`         | 文本对比 + 变更摘要 双Tab                         |
| 用例库   | `/testcases`    | 3级目录树 + 用例列表 + 导入/导出                  |
| 模板库   | `/templates`    | 用例结构模板 + Prompt模板 双Tab                   |
| 知识库   | `/knowledge`    | 4分类：企业规范/业务知识/历史用例/技术参考         |
| 回收站   | `/recycle`      | 30天自动清理 + 到期倒计时                         |
| 设置     | `/settings`     | AI配置 + Prompt管理 + 测试标准 + 操作日志          |

---

## 关键设计决策

| 决策                | 说明                                                                 |
| ------------------- | -------------------------------------------------------------------- |
| DDD 模块化          | 21 个模块各自封装，禁止跨模块直接调用 model 层                       |
| Prompt 在 engine 层 | router/service 不感知 Prompt 内容，engine 层统一管理                 |
| 懒加载 DB 引擎      | `database.py` 用 `@lru_cache` 延迟建立连接，避免导入时连接数据库     |
| 软删除统一          | 通过 `SoftDeleteMixin` 实现，禁止物理删除核心业务数据                |
| 测试点先于用例      | M04 确认「测什么」后才能进入 M05，前端确认按钮有未处理红色节点时置灰 |
| 两阶段 Diff         | 文本级（Myers / difflib）+ 语义级（LLM），防止业务影响被误判         |
| 幂等性保障          | 所有写入操作设计幂等，重试不产生重复数据，使用 upsert 而非 insert    |
