# Phase 3: AI 质量提升 - Context

**Gathered:** 2026-03-15
**Status:** Ready for planning

<domain>
## Phase Boundary

向量库中存储经过审查的高质量历史用例，所有 AI 模块使用重写后的 Prompt，RAG 检索结果可信。
不包括：用例库增强（Phase 4）、仪表盘重构（Phase 4）、回收站/模板库（Phase 5）。

历史数据源：`清洗后数据/` 目录，228 个 CSV 文件，约 12.9 万行，含信永中和和数栈平台两个产品线。

</domain>

<decisions>
## Implementation Decisions

### 审查运行方式

- 使用独立 Python 脚本（`scripts/review_testcases.py`），`uv run` 直接执行，无需额外服务
- 不依赖 Celery（当前全部是 stub），避免基础设施障碍
- **采样策略**：脚本支持 `--sample N` 参数，默认先每个 CSV 取前 N 条采样运行验证效果；确认质量后再跑全量
- 全量运行时脚本自动跳过已入库的用例（幂等，用 testcase_id 去重）
- **并行度**：标记为待定，用户后续根据 LLM API 限流情况决定（当前先顺序处理或简单 asyncio.gather）

### 审查报告呈现

- 脚本运行结束后在终端打印汇总表格（总数/通过/润色/丢弃/丢弃原因分组）
- 同时将详细结果持久化到 `scripts/review_report.json`，字段：`total`, `passed`, `polished`, `discarded`, `discard_reasons`（原因及频次）
- 不需要 UI 展示，纯运维操作场景

### 向量库清空范围

- **清空两个 collection**：`historical_testcases`（历史用例）和 `knowledge_chunks`（知识库文档）
- 理由：切换审查策略后两者可能混入脏数据；knowledge_chunks 当前用户数据少，影响有限
- 清空时机：脚本执行开始时清空，再重建

### knowledge_chunks 重建策略

- 脚本从 `knowledge` 模块 DB 表中读取已上传文档记录，重新向量化入库
- 不要求用户手动重新上传，脚本自动处理

### 嵌入模型

- **保持 zhipu embedding-3（2048 维）不变**
- GLM-5 只替换对话/分析场景（GLM-4-Flash → GLM-5），不影响嵌入流程
- 向量维度不变，清空重建无需修改 collection schema

### GLM-5 切换

- 设置页模型配置中可选择 `glm-5`，选择后全局生效（AI 分析和工作台）
- 后端 `llm_client.py` 已支持 zhipu provider 的模型参数传递，只需确认 `glm-5` 能正常调用

### Prompt 重写

- 6 个模块 Prompt 全部重写，保持现有四段式结构（身份声明/任务边界/输出规范/质量红线）
- 各模块身份声明需差异化（当前 6 个已有基础结构，主要补 Few-shot 和精细化约束）
- Few-shot 正负例：从清洗后历史用例中精选代表性正例（覆盖正常/异常/边界三种场景），负例手动编写（典型低质量用例模式）
- Few-shot 选取量：每个模块 2~3 条正例 + 1 条负例，不过度膨胀 Prompt

### SSE 换行渲染修复（RAG-06）

- 修复前端 SSE 内容中 `\n` 字符不转为换行的 bug
- 属于前端渲染层问题，修复点在流式内容处理逻辑（`useWorkbench` 或 StreamCursor 上游）

### Claude's Discretion

- 审查脚本并行度的具体数值（用户后续处理）
- Few-shot 示例的具体文字内容（从历史数据精选时由 Claude 判断）
- 重试/降级逻辑的指数退避参数
- `\n` 渲染 bug 的具体修复位置（需看代码确认）

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets

- `backend/app/engine/rag/retriever.py` — 已有 `TESTCASE_COLLECTION = "historical_testcases"` 常量，`retrieve_testcases()` 和 `retrieve_cases_as_context()` 函数，直接调用
- `backend/app/engine/rag/embedder.py` — 支持 zhipu/dashscope/openai 三种 provider，`EMBEDDING_DIMENSION = 2048`（zhipu），清空重建无需改维度
- `backend/app/engine/rag/retriever.py` — `delete_by_doc_id()` 可参考实现清空逻辑；`ensure_collection()` 已封装 collection 创建
- `backend/app/ai/prompts.py` — 现有 6 个模块 Prompt 已有四段式结构（DIAGNOSIS_SYSTEM、SCENE_MAP_SYSTEM 等），重写在此文件内完成
- `backend/app/ai/llm_client.py` — zhipu provider 已支持模型参数，GLM-5 切换只需配置 model 名称
- 历史数据字段：CSV 文件已是中文字段（用例标题/前置条件/步骤/预期结果/优先级），基本满足 RAG-07 要求

### Established Patterns

- RAG 入库流程：`chunk_by_*` → `embed_texts()` → `index_chunks()`，脚本直接复用
- 7 层 Prompt 组装：脚本修改 Layer 1（Module System Prompt）不影响其他层
- `settings.llm_provider` 控制默认 LLM 选择，已有 provider 切换逻辑

### Integration Points

- 审查脚本入口：`scripts/review_testcases.py`（新建），调用 `backend/app/engine/rag/` 和 `backend/app/ai/` 层
- Qdrant collection 清空：直接调用 `_get_client().delete_collection(name)` + `ensure_collection()` 重建
- knowledge 模块 DB 查询：从 `backend/app/modules/knowledge/` service 层查已上传文档记录
- 设置页 GLM-5 配置：`settings` 中的 `llm_provider`/`zhipu_model` 参数，前端设置页已有 AI 配置 UI

</code_context>

<specifics>
## Specific Ideas

- 审查脚本应在终端打印实时进度条（如 `Reviewing 3450/12900 (数栈平台/v0.2.0)...`），让用户能监控进度
- 采样模式输出格式示例：`[SAMPLE] Processed 50/228 files, 1250 cases. Pass: 892, Polish: 243, Discard: 115 (92.0% quality rate)`
- 丢弃原因分类建议：① 步骤缺失 ② 预期结果不具体 ③ 前置条件缺 SQL ④ 步骤不独立 ⑤ 无法修复

</specifics>

<deferred>
## Deferred Ideas

- 审查 UI 触发（设置页「开始审查」按钮 + 进度展示）—— Celery 补齐后（Phase 4 后期）
- 审查脚本并行度配置化（`--concurrency N`）—— 用户后续根据 API 限流决定
- 历史用例审查报告设置页展示 —— 如需要可在 Phase 4 补充 API + UI

</deferred>

---

*Phase: 03-ai*
*Context gathered: 2026-03-15*
