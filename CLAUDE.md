# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Sisyphus 测试用例生成平台

## 项目概述

Sisyphus 是一个 AI 驱动的功能测试用例生成平台，核心特性：

- 多 LLM 提供商支持（智谱 GLM、阿里百炼、MiniMax）
- Agent 编排系统：生成 Agent + 评审 Agent 协作
- RAG 增强：基于向量检索历史相似用例
- WebSocket 流式输出：实时进度反馈
- 多格式导出：CSV、Excel、Markdown

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | FastAPI 0.109 + SQLAlchemy 2.0 + AsyncIO + WebSocket |
| 数据库 | PostgreSQL + pgvector |
| 前端 | React 19 + TypeScript + Vite + Ant Design + Tailwind CSS |
| 状态管理 | TanStack Query + Zustand |

## 常用开发命令

### 后端 (backend/)

```bash
# 安装依赖
cd backend && uv sync

# 运行开发服务器
cd backend && uv run uvicorn app.main:app --reload

# 运行测试
cd backend && uv run pytest -v

# 运行测试（带覆盖率）
cd backend && uv run pytest --cov=app --cov-report=html
```

### 前端 (frontend/)

```bash
# 安装依赖
cd frontend && npm install

# 运行开发服务器
cd frontend && npm run dev

# 构建生产版本
cd frontend && npm run build

# 代码检查
cd frontend && npm run lint
```

### Docker 部署

```bash
docker-compose up -d
docker-compose logs -f backend
docker-compose down
```

## LLM 配置

### 智谱 Coding Plan 接入（重要）

Coding Plan 订阅制使用**专属 API 端点**，与普通 Token 付费不同：

| 计费方式 | API 端点 |
|---------|---------|
| Coding Plan 订阅制 | `https://open.bigmodel.cn/api/coding/paas/v4` |
| 普通 Token 付费 | `https://open.bigmodel.cn/api/paas/v4` |

⚠️ 使用 Coding Plan 必须配置正确的端点，否则会按 tokens 额外扣费！

### 环境变量配置 (.env)

```bash
# Coding Plan 配置
glm_api_key=你的API_Key
glm_base_url=https://open.bigmodel.cn/api/coding/paas/v4
glm_model=GLM-5
default_llm_provider=glm
```

### 支持的 LLM 提供商

| Provider | 模型 |
|----------|------|
| glm | glm-4, glm-4-plus, GLM-5 |
| alibaba | qwen-turbo, qwen-plus, qwen-max |
| minimax | abab5.5-chat, abab5.5s-chat |

### 配置优先级

1. 数据库配置（通过 `/settings` 页面）
2. 环境变量配置
3. 默认配置

## 核心架构

### Agent 系统

```
backend/app/agents/
├── base.py          # Agent 基类
├── generator.py     # 生成 Agent
├── reviewer.py      # 评审 Agent
└── orchestrator.py  # 编排器
```

**工作流程：**
1. 用户输入需求 → WebSocket 连接
2. RAG 检索历史相似用例
3. GeneratorAgent 生成测试用例
4. ReviewerAgent 评审用例质量
5. 不通过则反馈后重新生成（最多 3 次）

### LLM 集成

```
backend/app/llm/
├── base.py      # 抽象基类 LLMProvider
├── factory.py   # 工厂函数 create_llm_provider()
├── glm.py       # 智谱 GLM
├── alibaba.py   # 阿里百炼
└── minimax.py   # MiniMax
```

添加新 LLM 提供商：实现 `LLMProvider` 接口，注册到 `PROVIDER_MAP`。

### RAG 系统

```
backend/app/rag/
├── embeddings.py     # 向量嵌入
├── retriever.py      # 向量检索
└── prompt_builder.py # Prompt 模板
```

## API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/generate/ws` | WebSocket | 流式生成测试用例 |
| `/api/config/llm` | GET/PUT | LLM 配置 |
| `/api/files/upload` | POST | 上传文件 |
| `/api/testcases/` | GET | 获取用例列表 |
| `/api/export/csv` | POST | 导出 CSV |

## 数据库模型

| 模型 | 说明 |
|------|------|
| Project | 项目信息 |
| TestCase | 测试用例 |
| LLMConfig | LLM 配置（含加密 API Key） |
| File | 上传文件 |
| Requirement | 需求文档 |
