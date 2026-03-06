# Sisyphus 测试用例生成平台

[![CI](https://github.com/koco-co/Sisyphus-case-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/koco-co/Sisyphus-case-platform/actions/workflows/ci.yml)

AI 驱动的功能测试用例生成平台，支持多 LLM 提供商和 RAG 增强。

## ✨ 特性

- 🤖 **多 LLM 支持** - 智谱 GLM、阿里百炼、MiniMax
- 🔄 **Agent 编排** - 生成 Agent + 评审 Agent 协作
- 📚 **RAG 增强** - 基于向量检索历史相似用例
- ⚡ **实时反馈** - WebSocket 流式输出
- 📤 **多格式导出** - CSV、Excel、Markdown

## 🛠️ 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | FastAPI 0.109 + SQLAlchemy 2.0 + AsyncIO |
| 数据库 | PostgreSQL + pgvector |
| 前端 | React 19 + TypeScript + Vite + Ant Design |
| 状态管理 | TanStack Query + Zustand |
| 测试 | Vitest + Playwright + pytest |

## 🚀 快速开始

### Docker 部署（推荐）

```bash
docker-compose up -d
```

### 手动部署

**后端：**

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload
```

**前端：**

```bash
cd frontend
npm install
npm run dev
```

## 📖 文档

- [CLAUDE.md](./CLAUDE.md) - 项目架构和开发指南
- [CONTRIBUTING.md](./CONTRIBUTING.md) - 贡献指南

## 🧪 测试

| 类型 | 数量 | 命令 |
|------|------|------|
| 前端单元测试 | 49 | `cd frontend && npm run test:run` |
| 前端 E2E 测试 | 11 | `cd frontend && npm run test:e2e` |
| 后端测试 | 145 | `cd backend && uv run pytest -v` |

## 📊 项目状态

- ✅ 前端覆盖率：82.4%
- ✅ CI/CD：GitHub Actions
- ✅ 代码质量：ESLint + Ruff

## 🤝 贡献

欢迎贡献！请查看 [CONTRIBUTING.md](./CONTRIBUTING.md) 了解详情。

## 📄 许可证

MIT License
