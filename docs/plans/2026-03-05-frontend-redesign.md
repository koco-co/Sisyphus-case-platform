# Sisyphus 测试用例平台 - 前端重构设计文档

## 1. 概述

### 1.1 背景
上一轮实现的前端代码存在多处问题，用户体验不符合预期。需要重新设计为类似 Gemini/DeepSeek 的聊天式交互界面。

### 1.2 目标
- 简洁的聊天式交互界面
- 项目树导航管理需求和用例
- 流式输出的生成体验
- 可配置的导出模板系统

## 2. 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React + Vite)                   │
├─────────────────────────────────────────────────────────────────┤
│  页面：                                                          │
│  - HomePage        主聊天页（项目树 + 聊天区）                    │
│  - RequirementPage 需求详情页                                    │
│  - TestCasePage    用例详情页                                    │
│  - SettingsPage    设置页（LLM 配置）                            │
├─────────────────────────────────────────────────────────────────┤
│                        Backend (FastAPI)                         │
├─────────────────────────────────────────────────────────────────┤
│  保留：Agent、RAG、文档解析器                                     │
│  重构：API 层、数据模型                                           │
├─────────────────────────────────────────────────────────────────┤
│  数据库：PostgreSQL + pgvector                                   │
│  文件存储：本地文件系统 / MinIO（可配置切换）                      │
└─────────────────────────────────────────────────────────────────┘
```

## 3. 界面设计

### 3.1 主页面布局

```
┌───────────────────────────────────────────────────────────────┐
│  Logo                                    用户头像/设置         │
├────────────┬──────────────────────────────────────────────────┤
│            │                                                  │
│  📁 项目树  │         欢迎使用测试用例生成平台                  │
│  ├─ 项目A   │                                                  │
│  │ ├─ 需求1 │         ┌────────────────────────────────────┐  │
│  │ └─ 需求2 │         │                                    │  │
│  ├─ 项目B   │         │     [大的聊天输入框]                │  │
│  │ └─ ...   │         │     📎 上传文件                    │  │
│  └─ ...    │         │     ──────────────────────────────  │  │
│            │         │     发送 →                          │  │
│  + 新建项目 │         │                                    │  │
│            │         └────────────────────────────────────┘  │
│            │                                                  │
└────────────┴──────────────────────────────────────────────────┘
```

### 3.2 页面路由结构

| 路由 | 页面 | 说明 |
|------|------|------|
| `/` | HomePage | 主聊天页（项目树 + 聊天区） |
| `/projects/:id` | HomePage | 同主页，但选中指定项目 |
| `/requirements/:id` | RequirementPage | 需求详情页 |
| `/testcases/:id` | TestCasePage | 用例详情页 |
| `/settings` | SettingsPage | 设置页（LLM 配置） |

### 3.3 三层下钻结构

```
侧边栏                    用例列表页                  用例详情页
┌──────────────┐         ┌─────────────────────┐    ┌─────────────────────┐
│ 📁 项目A      │         │ ← 返回  需求：登录功能 │    │ ← 返回  用例：正常登录 │
│   📝 登录功能  │ ──────> │─────────────────────│    │─────────────────────│
│   📝 支付流程  │         │ 📋 用例1: 正常登录    │    │ 标题: 正常登录        │
│ 📁 项目B      │         │ 📋 用例2: 密码错误    │    │ 优先级: P1           │
│   ...        │         │ 📋 用例3: 账号不存在  │    │ 前置条件: 已注册账号  │
└──────────────┘         │ ...                 │    │─────────────────────│
                         └─────────────────────┘    │ 序号│步骤    │预期    │
                         点击用例 ────────────────>  │  1  │输入账号│显示密码│
                                                    │  2  │输入密码│进入首页│
                                                    └─────────────────────┘
```

## 4. 交互流程

### 4.1 主流程

```
用户上传文档
    │
    ▼
FilePreview 流式渲染文档内容
    │
    ▼
用户点击"开始生成"
    │
    ▼
WebSocket 连接，流式输出：
  - "正在分析需求结构..."
  - "识别到 3 个功能模块..."
  - "生成测试用例..."
    │
    ▼
用户可继续对话修改
    │
    ▼
用户点击"保存"
    │
    ▼
调用 POST /api/generate/save
  - 创建 requirement 记录
  - 创建 test_case 记录
  - 关联 conversation 历史
    │
    ▼
侧边栏项目树自动刷新
```

### 4.2 文件上传流程

1. 用户点击上传按钮或拖拽文件
2. 文件上传到服务器
3. 服务器流式解析并返回 Markdown 内容
4. 前端实时渲染预览
5. 用户确认后开始生成

## 5. 数据模型

### 5.1 项目表 (projects)

```sql
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### 5.2 需求表 (requirements)

```sql
CREATE TABLE requirements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,

    -- 结构化需求内容 (JSONB)
    -- { modules: [{ name, description, features: [{ name, description, input, output, exceptions }] }] }
    content JSONB NOT NULL DEFAULT '{}',

    -- 原始文档元数据
    source_file_id UUID REFERENCES files(id),

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### 5.3 文件表 (files)

```sql
CREATE TABLE files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename VARCHAR(255) NOT NULL,
    original_name VARCHAR(255) NOT NULL,
    mime_type VARCHAR(100),
    size BIGINT,

    -- 存储类型: 'local' | 'minio'
    storage_type VARCHAR(20) DEFAULT 'local',
    -- 存储路径或对象键
    storage_path VARCHAR(500),

    -- 解析后的文本内容（用于 RAG）
    parsed_content TEXT,

    created_at TIMESTAMP DEFAULT NOW()
);
```

### 5.4 测试用例表 (test_cases)

```sql
CREATE TABLE test_cases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    requirement_id UUID REFERENCES requirements(id) ON DELETE CASCADE,

    title VARCHAR(500) NOT NULL,
    priority VARCHAR(10) DEFAULT 'P2',  -- P0, P1, P2, P3
    preconditions TEXT,

    -- 测试步骤 (JSONB)
    -- [{ step: 1, action: '...', expected: '...' }]
    steps JSONB NOT NULL DEFAULT '[]',

    -- 标签（可选）
    tags TEXT[] DEFAULT '{}',

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### 5.5 导出模板表 (export_templates)

```sql
CREATE TABLE export_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,

    -- 字段配置
    -- { fields: ['title', 'priority', ...], order: {...} }
    field_config JSONB NOT NULL DEFAULT '{}',

    -- 格式配置
    -- { format: 'csv', delimiter: ',', header_names: {...} }
    format_config JSONB NOT NULL DEFAULT '{}',

    -- 条件过滤
    -- { priority: ['P0', 'P1'], tags: [...] }
    filter_config JSONB NOT NULL DEFAULT '{}',

    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 5.6 对话历史表 (conversations)

```sql
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    requirement_id UUID REFERENCES requirements(id) ON DELETE CASCADE,

    -- 消息列表 (JSONB)
    -- [{ role: 'user'/'assistant', content: '...', timestamp: '...' }]
    messages JSONB NOT NULL DEFAULT '[]',

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### 5.7 用户配置表 (user_configs)

```sql
CREATE TABLE user_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- LLM 配置
    -- { provider: 'openai'/'zhipu'/'alibaba'/'minimax',
    --   api_key: '...', model: '...' }
    llm_config JSONB NOT NULL DEFAULT '{}',

    updated_at TIMESTAMP DEFAULT NOW()
);
```

## 6. 后端 API 设计

### 6.1 路由结构

```
API 路由结构
├── /api/projects
│   ├── GET    /                    # 获取项目列表
│   ├── POST   /                    # 创建项目
│   ├── GET    /{id}                # 获取项目详情
│   ├── PUT    /{id}                # 更新项目
│   └── DELETE /{id}                # 删除项目
│
├── /api/requirements
│   ├── GET    /{id}                # 获取需求详情（含结构化内容）
│   ├── PUT    /{id}                # 更新需求
│   └── DELETE /{id}                # 删除需求
│
├── /api/files
│   ├── POST   /upload              # 上传文件（返回解析内容，流式）
│   ├── GET    /{id}                # 获取文件信息
│   └── GET    /{id}/content        # 获取文件内容（流式返回）
│
├── /api/generate
│   ├── WebSocket /ws               # 流式生成（对话 + 用例生成）
│   └── POST   /save                # 保存生成的需求 + 用例
│
├── /api/testcases
│   ├── GET    /requirement/{id}    # 获取需求下的用例列表
│   ├── GET    /{id}                # 获取用例详情
│   ├── PUT    /{id}                # 更新用例
│   └── DELETE /{id}                # 删除用例
│
├── /api/export
│   ├── GET    /templates           # 获取导出模板列表
│   ├── POST   /templates           # 创建导出模板
│   ├── PUT    /templates/{id}      # 更新模板
│   ├── DELETE /templates/{id}      # 删除模板
│   └── POST   /                    # 导出用例（按模板配置）
│
└── /api/config
    ├── GET    /llm                 # 获取 LLM 配置
    └── PUT    /llm                 # 更新 LLM 配置
```

### 6.2 关键 API 说明

| API | 说明 |
|-----|------|
| `POST /api/files/upload` | 上传文件，**流式返回**解析后的 Markdown 内容 |
| `WebSocket /api/generate/ws` | 对话式生成，支持流式输出思考和用例 |
| `POST /api/generate/save` | 用户确认后保存需求和用例到数据库 |
| `POST /api/export/` | 按模板配置导出，支持字段选择、条件过滤 |

## 7. 前端组件设计

### 7.1 目录结构

```
src/
├── components/
│   ├── Layout/
│   │   ├── AppLayout.tsx          # 整体布局（侧边栏 + 主内容区）
│   │   └── AppSidebar.tsx         # 项目树侧边栏
│   │
│   ├── Chat/
│   │   ├── ChatContainer.tsx      # 聊天容器
│   │   ├── ChatInput.tsx          # 输入框 + 上传按钮
│   │   ├── ChatMessage.tsx        # 单条消息渲染
│   │   ├── FilePreview.tsx        # 文件预览（流式 Markdown）
│   │   └── StreamingText.tsx      # 流式文本渲染组件
│   │
│   ├── Requirement/
│   │   ├── RequirementDetail.tsx  # 结构化需求展示
│   │   └── ModuleCard.tsx         # 功能模块卡片
│   │
│   ├── TestCase/
│   │   ├── TestCaseList.tsx       # 用例列表
│   │   ├── TestCaseCard.tsx       # 用例卡片
│   │   └── TestCaseDetail.tsx     # 用例详情（步骤表格）
│   │
│   └── Export/
│       ├── TemplateManager.tsx    # 模板管理
│       ├── TemplateEditor.tsx     # 模板编辑器
│       └── ExportModal.tsx        # 导出弹窗
│
├── pages/
│   ├── Home.tsx                   # 主页（聊天界面）
│   ├── Requirement.tsx            # 需求详情页
│   ├── TestCase.tsx               # 用例详情页
│   └── Settings.tsx               # 设置页
│
├── hooks/
│   ├── useWebSocket.ts            # WebSocket 连接
│   ├── useStreaming.ts            # 流式数据处理
│   └── useProjects.ts             # 项目管理
│
└── stores/
    └── useAppStore.ts             # 全局状态（Zustand）
```

## 8. 后端重构计划

### 8.1 保留的核心模块

| 模块 | 路径 | 说明 |
|------|------|------|
| Agent 系统 | `backend/app/agents/` | 保留 Generator Agent、Reviewer Agent、Orchestrator |
| RAG 检索 | `backend/app/rag/` | 保留 Embeddings、Retriever、PromptBuilder |
| 文档解析 | `backend/app/plugins/` | 保留 TXT、MD、PDF 解析器 |
| LLM 接入 | `backend/app/llm/` | 保留各 LLM 适配器 |

### 8.2 需要重构的模块

| 模块 | 变更内容 |
|------|----------|
| **数据模型** | 新增 `files`, `requirements`, `conversations`, `export_templates` 表 |
| **API 层** | 重构路由结构，新增流式上传、导出模板等 API |
| **文件存储** | 新增混合存储服务（本地/MinIO 切换） |
| **用例生成** | 调整 WebSocket 协议，支持结构化需求输出 |

### 8.3 新增模块

| 模块 | 路径 | 说明 |
|------|------|------|
| 文件存储服务 | `backend/app/services/storage.py` | 本地/MinIO 混合存储 |
| 导出服务 | `backend/app/services/export.py` | 模板化导出 CSV/Excel/JSON |
| 需求解析 | `backend/app/services/requirement_parser.py` | 文档 → 结构化需求 |

### 8.4 重构后的后端结构

```
backend/app/
├── api/                    # API 路由（重构）
│   ├── projects.py
│   ├── requirements.py     # 新增
│   ├── files.py            # 新增（流式上传）
│   ├── generate.py         # 重构（WebSocket 协议）
│   ├── testcases.py        # 新增
│   ├── export.py           # 新增
│   └── config.py
│
├── services/               # 业务服务（新增）
│   ├── storage.py          # 文件存储
│   ├── export.py           # 导出服务
│   └── requirement_parser.py
│
├── agents/                 # 保留
├── rag/                    # 保留
├── llm/                    # 保留
├── plugins/                # 保留
│
└── models/                 # 数据模型（重构）
    ├── project.py
    ├── requirement.py      # 新增
    ├── file.py             # 新增
    ├── test_case.py        # 重构
    ├── export_template.py  # 新增
    ├── conversation.py     # 新增
    └── user_config.py
```

## 9. 需要删除的旧文件

以下文件将被新实现替代：

```
# 前端（将被删除或重写）
frontend/src/components/ChatInterface.tsx      # → 新的 Chat/ 组件
frontend/src/components/DocumentUpload.tsx     # → 新的 ChatInput.tsx
frontend/src/components/TestCaseTable.tsx      # → 新的 TestCase/ 组件
frontend/src/pages/CaseGeneration.tsx         # → 新的 Home.tsx
frontend/src/hooks/useWebSocket.ts            # → 重构

# 后端（重构或删除）
backend/app/api/cases.py                      # → testcases.py
backend/app/api/documents.py                  # → files.py
```

## 10. 文件存储方案

采用混合存储策略，通过配置切换：

- **开发环境**：本地文件系统（`./uploads/` 目录）
- **生产环境**：MinIO（兼容 S3 协议）

数据库存储文件元数据（路径、大小、类型），实际文件存储在配置的后端。

## 11. 实施计划

```
Phase 1: 基础架构重构
├── 1.1 数据库迁移脚本（新表结构）
├── 1.2 文件存储服务（本地/MinIO 混合）
├── 1.3 后端 API 重构（新路由结构）
└── 1.4 前端路由和布局（新页面结构）

Phase 2: 核心功能实现
├── 2.1 主聊天界面（输入框 + 文件上传）
├── 2.2 文件流式上传和预览
├── 2.3 WebSocket 流式生成（对话 + 用例）
└── 2.4 侧边栏项目树

Phase 3: 详情页面
├── 3.1 需求详情页（结构化需求展示）
├── 3.2 用例列表页
└── 3.3 用例详情页（步骤表格）

Phase 4: 导出和配置
├── 4.1 导出模板管理
├── 4.2 用例导出功能
└── 4.3 LLM 配置页面
```
