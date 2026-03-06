# 贡献指南

感谢你对 Sisyphus 测试用例生成平台感兴趣！

## 开发环境设置

### 前置要求

- Node.js 20+
- Python 3.12+
- PostgreSQL 16 + pgvector
- Docker (可选)

### 前端设置

```bash
cd frontend
npm install
npm run dev
```

### 后端设置

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload
```

### 环境变量

复制示例配置文件：

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

## 开发工作流

### 1. 创建分支

```bash
git checkout -b feature/your-feature-name
```

### 2. 进行更改

- 遵循现有的代码风格
- 添加必要的测试
- 更新相关文档

### 3. 运行测试

```bash
# 前端测试
cd frontend
npm run test:run
npm run test:e2e

# 后端测试
cd backend
uv run pytest -v
```

### 4. 提交更改

使用约定式提交格式：

```
feat: 添加新功能
fix: 修复 bug
docs: 文档更新
test: 测试相关
refactor: 代码重构
chore: 构建/工具相关
```

### 5. 创建 Pull Request

填写 PR 模板中的所有必填项。

## 代码规范

### 前端

- 使用 TypeScript
- 遵循 ESLint 规则
- 组件使用函数式组件 + Hooks
- 测试覆盖率 ≥ 80%

### 后端

- 使用 Python 3.12+ 特性
- 遵循 Ruff 规则
- 使用异步函数
- 测试覆盖率 ≥ 80%

## 项目结构

```
├── frontend/          # React 前端
│   ├── src/
│   │   ├── components/  # UI 组件
│   │   ├── hooks/       # 自定义 Hooks
│   │   ├── pages/       # 页面组件
│   │   └── test/        # 测试配置
│   └── e2e/             # E2E 测试
├── backend/           # FastAPI 后端
│   └── app/
│       ├── api/         # API 端点
│       ├── agents/      # Agent 系统
│       ├── llm/         # LLM 集成
│       └── tests/       # 测试
└── .github/           # CI/CD 配置
```

## 获取帮助

如有问题，请创建 Issue 或联系维护者。
