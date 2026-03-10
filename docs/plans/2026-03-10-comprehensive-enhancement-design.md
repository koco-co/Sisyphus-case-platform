# Sisyphus-Y 综合增强设计方案

> 日期：2026-03-10
> 状态：待审批
> 范围：工作台修复、CSV 清洗管线、AI 配置增强、progress.json 重写

---

## 1. 问题陈述

当前 Sisyphus-Y 平台有四个待解决的主要方向：

1. **工作台体验问题**：后端 `/sessions/{id}/messages` 不返回关联用例数据，导致 ChatArea 中的 `message.cases` 始终为空，消息内嵌用例卡片无法展示。同时需要与原型图对齐细节。
2. **历史用例清洗**：`待清洗数据/` 下 65 个 CSV 文件（158K 行），需 LLM 辅助清洗后写入 PostgreSQL + Qdrant，目前仅有基础解析框架。
3. **AI 模型配置页面不完整**：缺少 API Key 手动输入、向量模型配置、连接测试、术语悬浮释义。
4. **progress.json 需要重写**：当前格式与新需求不符，需细粒度任务拆分。

---

## 2. 推荐方案与取舍

### 2.1 工作台修复

**方案 A（推荐）：后端补全 + 前端微调**
- 修改 `/sessions/{id}/messages` 接口，JOIN 查询关联 TestCase，返回 `cases` 字段
- 前端 ChatArea 已有 CaseCard 渲染逻辑（lines 95-109），数据到位即可生效
- 对照原型图微调左栏（需求导航加测试点子列表）、中栏（模式指示器）、右栏（统计面板）
- 工作量：小，主要是后端数据层修改

**方案 B：前端独立请求用例数据**
- 前端在加载消息后，额外请求 `/sessions/{id}/cases`，按 created_at 时间匹配到对应消息
- 优点：不改后端接口
- 缺点：时间匹配不可靠，前端逻辑复杂

**方案 C：重构消息模型，用例作为消息的嵌入类型**
- 新增消息类型 `case_embed`，直接在消息表中存储结构化用例引用
- 优点：最干净的数据模型
- 缺点：需要改 schema 和迁移，工作量大

**决定：方案 A** — 最小改动实现效果。

### 2.2 CSV 清洗管线

**方案 A（推荐）：批处理 + LLM 流水线**
- 分 3 阶段：① 解析标准化 → ② LLM 清洗 → ③ 写入 PG+Qdrant
- 使用 Celery 异步任务处理，避免阻塞 API
- LLM 调用使用 GLM-4-Flash，按批次（10 条/批）发送减少 API 调用
- 清洗后用例写入现有 `test_cases` 表（source='imported'），新增 `clean_status`、`quality_score`、`original_raw` 字段
- 前端在用例管理页增加"导入清洗"标签页

**方案 B：纯规则清洗（不用 LLM）**
- 使用正则+规则清洗
- 优点：快、免费
- 缺点：无法补全缺失的前置条件/步骤描述，质量有限

**方案 C：实时清洗（用户触发逐文件清洗）**
- 用户上传 CSV 后实时展示清洗进度
- 优点：交互性好
- 缺点：158K 行数据 LLM 清洗耗时巨大，不适合实时

**决定：方案 A** — 批处理最适合大量数据清洗场景。

### 2.3 AI 模型配置增强

**方案 A（推荐）：扩展现有 ai_config 模块**
- 在现有 `AiConfiguration` 模型中新增字段：
  - `api_keys: dict` — 加密存储各提供商 API Key（使用 Fernet 对称加密）
  - `vector_model: dict` — 向量模型配置（provider、model、dimension）
- 前端 AIModelSettings 组件扩展：API Key 输入区、向量模型区、连接测试按钮、参数 Tooltip
- 新增后端 `/ai-config/test-connection` 端点

**方案 B：独立密钥管理模块**
- 新建 `secrets` 模块管理 API Key
- 过度设计，当前规模不需要

**决定：方案 A** — 在现有模块基础上扩展。

---

## 3. 架构设计

### 3.1 工作台数据流

```
用户发送消息 → POST /generation/sessions/{id}/chat
  → SSE 流式返回 thinking/content/done 事件
  → done 事件触发后端自动解析用例 → 写入 test_cases 表
  → 前端 onDone 回调 → 重新加载 messages（含 cases）+ 右栏 testCases

GET /sessions/{id}/messages 返回:
[{
  id, role, content, thinking_content, created_at,
  cases: [{ id, case_id, title, priority, steps, ... }]  // ← 新增
}]
```

### 3.2 CSV 清洗管线架构

```
┌─────────────┐    ┌──────────────────┐    ┌───────────────┐    ┌───────────┐
│  CSV 文件    │ →  │ 解析 & 标准化    │ →  │ LLM 清洗引擎  │ →  │ 写入层    │
│ 65 个文件    │    │ - 列映射         │    │ - GLM-4-Flash │    │ - PG      │
│ 158K 行     │    │ - HTML 标签剥离  │    │ - 前置条件补全│    │ - Qdrant  │
│             │    │ - 空值统一       │    │ - 步骤独立化  │    │           │
└─────────────┘    └──────────────────┘    │ - 预期明确化  │    └───────────┘
                                           │ - 质量评分    │
                                           └───────────────┘

Celery 任务编排:
  clean_csv_batch_task(file_path, batch_size=10)
    → parse_and_normalize()
    → llm_clean_batch(cases[])       # 每 10 条一批
    → score_and_filter()             # 质量评分 + 处置
    → persist_to_pg()                # 写 test_cases 表
    → vectorize_and_index()          # 写 Qdrant
```

### 3.3 数据模型变更

```python
# TestCase 表新增字段
clean_status: str | None     # 'excellent' / 'good' / 'polished' / 'discarded'
quality_score: float | None  # 0.0 - 5.0
original_raw: dict | None    # 清洗前原始数据（JSONB）

# AiConfiguration 表新增字段
api_keys: dict | None        # {"zhipu": "encrypted_key", "dashscope": "encrypted_key"}
vector_config: dict | None   # {"provider": "zhipu", "model": "embedding-3", "dimension": 2048}
```

### 3.4 AI 配置增强

```
前端设置面板
├── LLM 模型区域
│   ├── 提供商下拉（智谱/阿里百炼/OpenAI/Ollama）
│   ├── API Key 输入框（脱敏显示 sk-****...****）
│   ├── Model 名称文本框
│   ├── Base URL（Ollama 时可编辑）
│   ├── 参数滑块（Temperature? / Top-P? / Max Tokens?）  ← 带 Tooltip
│   └── 「测试连接」按钮
│
├── 向量模型区域
│   ├── 向量模型提供商下拉
│   ├── 模型名称
│   ├── 向量维度（已知模型自动填充）
│   └── 「测试连接」按钮
│
└── 维度变更确认弹窗 → Celery 异步重建任务

后端端点:
  POST /ai-config/test-llm        → 发送 "你好" 测试消息
  POST /ai-config/test-embedding  → 向量化测试文本
  POST /ai-config/rebuild-vectors → 触发 Qdrant 重建
```

---

## 4. 组件清单

### 4.1 后端变更

| 文件 | 变更 |
|------|------|
| `modules/generation/router.py` | messages 接口返回关联 cases |
| `modules/generation/service.py` | 新增 list_messages_with_cases 方法 |
| `modules/testcases/models.py` | 新增 clean_status/quality_score/original_raw 字段 |
| `modules/import_clean/service.py` | 新增 LLM 批量清洗逻辑 |
| `modules/import_clean/router.py` | 新增批量清洗触发/进度查询端点 |
| `engine/import_clean/cleaner.py` | **新建** LLM 清洗引擎（Prompt + 评分） |
| `modules/ai_config/models.py` | 新增 api_keys/vector_config 字段 |
| `modules/ai_config/router.py` | 新增 test-llm/test-embedding/rebuild-vectors 端点 |
| `modules/ai_config/service.py` | 新增连接测试和密钥加密逻辑 |
| `core/encryption.py` | **新建** Fernet 对称加密工具 |
| Alembic migration | 新增字段迁移 |

### 4.2 前端变更

| 文件 | 变更 |
|------|------|
| `workbench/_components/RequirementNav.tsx` | 增加测试点子列表展开 |
| `workbench/_components/ChatArea.tsx` | 确认 CaseCard 渲染正常（已实现） |
| `settings/_components/AIModelSettings.tsx` | 重构：增加 API Key/向量模型/Tooltip |
| `settings/_components/ConnectionTestButton.tsx` | **新建** 连接测试按钮组件 |
| `settings/_components/ParamTooltip.tsx` | **新建** 参数术语释义 Tooltip |
| `testcases/` | 增加"导入清洗"标签页 + 清洗前后对比视图 |
| `hooks/useAiConfig.ts` | 扩展支持 api_keys/vector_config |

---

## 5. 不做什么（YAGNI）

- ❌ 不做实时 CSV 逐行清洗进度展示（批处理即可）
- ❌ 不做多租户 API Key 隔离（当前单团队使用）
- ❌ 不做 CaseCard 拖拽排序（不在需求范围）
- ❌ 不做 SSE 流式中途展示部分生成的 CaseCard（流完成后整体展示）

---

## 6. 风险与应对

| 风险 | 概率 | 应对 |
|------|------|------|
| 158K 行 LLM 清洗耗时长 | 高 | 批处理 + Celery 异步；先处理 P0 产品线 |
| GLM-4-Flash API 速率限制 | 中 | 指数退避重试 + 批次间间隔 |
| 清洗质量不稳定 | 中 | 评分机制 + 人工抽检入口 |
| 向量维度变更导致数据丢失 | 低 | 变更前确认弹窗 + 旧 collection 备份 |

---

## 7. 测试策略

- **工作台**：启动前后端 → 创建 session → 发送消息 → 验证 CaseCard 渲染
- **CSV 清洗**：单元测试 CSV 解析 → 集成测试 LLM 清洗 → 端到端测试 PG+Qdrant 写入
- **AI 配置**：单元测试加密/解密 → 集成测试连接测试端点 → 前端 E2E 测试
