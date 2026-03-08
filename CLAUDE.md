# CLAUDE.md

## 项目概述

Sisyphus-case-platform 是 AI 驱动的企业级功能测试用例自动生成平台，面向数据中台场景，覆盖需求录入 → 健康诊断 → 测试点分析 → 用例生成 → 执行回流的完整测试生命周期。

核心理念：显式拆分「测什么」（测试点/场景地图）和「怎么测」（用例步骤），通过评审节点前置拦截方向错误。

## 架构

- **后端**: FastAPI (Python 3.12) — DDD 模块化架构，21 个业务模块在 `backend/app/modules/`
- **前端**: Next.js 16 App Router (TypeScript) — 页面与后端模块对应，在 `frontend/src/app/(main)/`
- **AI 引擎**: LangChain + LangGraph，支持 GPT-4o / Claude / Ollama 多模型切换
- **存储**: PostgreSQL (业务) + Redis (缓存/队列) + Qdrant (向量) + MinIO (文件)
- **异步任务**: Celery + Redis

## 模块对照表

| 后端模块 | 前端页面 | 职责 |
|---|---|---|
| `modules/auth/` | `(auth)/login/` | 认证与权限 |
| `modules/products/` | `(main)/products/`, `iterations/`, `requirements/` | 子产品/迭代/需求三级管理 (M00) |
| `modules/uda/` | — | 文档解析引擎，UDA 层 (M01) |
| `modules/import_clean/` | — | 历史数据导入清洗 (M02) |
| `modules/diagnosis/` | `(main)/diagnosis/` | 需求健康诊断 (M03) |
| `modules/scene_map/` | `(main)/scene-map/` | 测试点分析 & 场景地图 (M04) |
| `modules/generation/` | `(main)/workbench/` | 对话式用例生成工作台 (M05) |
| `modules/testcases/` | `(main)/testcases/` | 用例管理中心 (M06) |
| `modules/diff/` | `(main)/diff/` | 需求 Diff & 变更影响 (M07) |
| `modules/coverage/` | `(main)/coverage/` | 需求覆盖度矩阵 (M08) |
| `modules/test_plan/` | — | 迭代测试计划 (M09) |
| `modules/templates/` | — | 用例模板库 (M10) |
| `modules/knowledge/` | `(main)/knowledge/` | 知识库管理 (M11) |
| `modules/export/` | — | 用例导出与集成 (M12) |
| `modules/execution/` | — | 执行结果回流 (M13) |
| `modules/analytics/` | `(main)/analytics/` | 质量分析看板 (M14) |
| `modules/notification/` | — | 通知系统 (M16) |
| `modules/search/` | — | 全局搜索 (M17) |
| `modules/collaboration/` | — | 协作功能 (M18) |
| `modules/dashboard/` | `(main)/` | 首页仪表盘 (M19) |
| `modules/audit/` | — | 操作审计日志 (M20) |
| `modules/recycle/` | — | 回收站 (M21) |

## 开发规范

### 环境管理

- Python 环境: **uv**（不使用 pip/conda/poetry）
- 前端包管理: **bun**（不使用 npm/yarn/pnpm）

### 代码质量

- Python lint/format: **ruff** (`uv run ruff check .` + `uv run ruff format .`)
- Python 类型检查: **pyright** (`uv run pyright app/`，standard 模式)
- 前端 lint/format: **Biome** (`bunx biome check .`)
- 前端类型检查: **tsc** (`bunx tsc --noEmit`)

### 命名约定

- Python: `snake_case`（文件、变量、函数），`PascalCase`（类）
- TypeScript: `camelCase`（变量、函数），`PascalCase`（组件、类型）
- API 路由: `kebab-case`（`/api/scene-map/generate`）
- 数据库表名: `snake_case` 复数（`test_cases`，`scene_nodes`）

### 后端模块结构

每个业务模块必须包含：

```
modules/<name>/
├── __init__.py
├── router.py    # API 路由，只做参数校验和调用 service
├── models.py    # SQLAlchemy ORM 模型
├── schemas.py   # Pydantic 请求/响应模型
└── service.py   # 业务逻辑，接收 AsyncSession 作为参数
```

### Git 规范

- 分支: `feat/<module>-<desc>`, `fix/<desc>`, `docs/<desc>`
- Commit: Conventional Commits（`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`）
- PR 到 main 必须更新 `CHANGELOG.md`

### 测试

- 后端: pytest + pytest-asyncio，`asyncio_mode = "auto"`
- 命名: `tests/unit/test_<module>/test_<feature>.py`
- Fixture: 公共放 `tests/conftest.py`，模块级放模块测试目录内

### 软删除

所有核心业务表均通过 `SoftDeleteMixin` 支持软删除（`deleted_at` 字段）。查询时必须过滤 `WHERE deleted_at IS NULL`。

## 常用命令

```bash
# 一键启动开发环境
./init.sh

# 后端
cd backend
uv sync --all-extras           # 安装依赖
uv run ruff check .            # lint 检查
uv run ruff format .           # 格式化
uv run pyright app/            # 类型检查
uv run pytest -v               # 运行测试
uv run pytest --cov=app        # 测试 + 覆盖率
uv run alembic upgrade head    # 数据库迁移
uv run alembic revision --autogenerate -m "描述"  # 生成迁移文件
uv run uvicorn app.main:app --reload --port 8000  # 启动开发服务器

# 前端
cd frontend
bun install                    # 安装依赖
bunx biome check .             # lint + format 检查
bunx biome check --write .     # 自动修复
bunx tsc --noEmit              # 类型检查
bun run build                  # 生产构建
bun dev                        # 启动开发服务器

# Docker
docker compose -f docker/docker-compose.yml up -d    # 启动基础设施
docker compose -f docker/docker-compose.yml down     # 停止
docker compose -f docker/docker-compose.yml logs -f  # 查看日志
```

## 关键设计决策

1. **DDD 模块化**：21 个业务模块各自包含 router/models/schemas/service，后端边界清晰
2. **懒加载 DB 引擎**：`database.py` 使用 `@lru_cache` 延迟创建引擎，避免导入时连接
3. **软删除统一**：所有业务表通过 `SoftDeleteMixin` 支持 `deleted_at`，不硬删除数据
4. **测试点先于用例**：核心流程先确认「测什么」（M04），再生成「怎么测」（M05）
5. **两阶段 Diff**：文本级（Myers）+ 语义级（LLM），防止业务影响被误判
