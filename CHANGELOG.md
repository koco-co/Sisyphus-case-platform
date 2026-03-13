# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **用例目录管理** — 支持多级目录（最多 3 层）：新建、行内双击重命名（Enter 确认/Esc 取消）、删除（含回收站软删除）；系统目录「未分类」不可删除/重命名
- **FolderTree dnd-kit 拖拽排序** — 同级目录间拖拽排序，结果持久化到 DB；右键菜单提供重命名/删除入口
- **用例导入增强** — 支持 4 种格式（Excel/CSV/JSON/XMind）；新增导入模板下载（xlsx/csv/xmind）；目录选择器默认「未分类」；逐条重复检测策略（覆盖/跳过/重命名）；成功后 Toast 汇报「导入 N 条/跳过 M 条/覆盖 K 条」
- **XMind 解析** — 后端接入 `xmindparser`，支持 xmind2026 格式；递归展平思维导图节点为测试用例行
- **导入解析 API** — `POST /testcases/import/parse-file`（解析+预览）、`POST /testcases/import/check-duplicates`（重复检测）、`POST /testcases/import/batch`（带策略批量导入）
- **DB 迁移** — `is_system` 字段加入 `test_case_folders`；`requirement_id` 改为可空（支持导入用例无需关联需求）；多 Alembic head 合并为单一 `ec4b13b4028c`

### Fixed
- **GlobalSearch.tsx 类型错误** — `useRef` 初始值显式传 `undefined`；`SearchResultItem` 类型映射修正
- **testcases/page.tsx** — `ExportDialog` 改为默认导入；`selectedIds.length` → `selectedIds.size`

- **6 模块 System Prompt 重写** — 每个模块包含独立的 ①身份声明 ②任务边界 ③输出规范 ④质量红线 四部分结构，各模块角色声明差异化
- **Prompt 编辑器「默认值」badge** — 未自定义的模块显示「默认值」标识，保存后显示保存时间
- **需求文档标准模板** — `public/templates/需求文档模板.md` + `.docx`，内置功能背景/功能描述（含业务规则/异常处理/数据约束）/接口说明/非功能要求章节
- **UDA 结构化解析端点** — `POST /uda/parse-structure`，解析文档后按章节拆分返回条目列表 + 置信度评分（0.2~0.9），不入库
- **需求上传两步对话框** — Step 1 含模板下载入口及引导文案，Step 2 展示解析条目（可编辑/删除/添加），低置信度时显示非阻断警告，确认后才保存，不自动触发 AI 分析

### Fixed
- **Prompt 管理器 key 错误** — `diff_semantic` 修正为 `diff`，与后端 `_MODULE_PROMPTS` 一致
- **GET /ai-config/prompts 空列表问题** — 首次安装无 DB 记录时，现在始终返回全部 6 个模块，默认值标注 `is_default: true`
- **文案 typo** — 「需求需求分析时」→「需求分析时」
- **历史记录缺少预览** — 历史面板每条记录新增 80 字符内容预览

### Changed
- **全站「诊断」→「分析」文案替换** — 前端 progress、useDashboard、useDiagnosis 中 UI 文本；后端 diagnosis/search/dashboard 模块注释、日志、Prompt 文案（变量名/路由/类名保持不变）

## [2.0.0-rc] - 2026-03-13

### Added

- **全面 UI 重构** — 移除 antd，统一使用 shadcn/ui + sy-* 设计 token
- **导航重构** — 13 → 9 菜单项，新增「分析台」（含 4 子 Tab）和「工作台」合并页
- **AI 模型配置增强** — ModelConfiguration CRUD，7 预设提供商（含 DeepSeek/月之暗面）
- **Prompt 管理系统** — 6 模块 Prompt 编辑器 + 保存历史 + 版本回滚
- **仪表盘质量分析** — 双 Tab（项目概览 + 质量分析），柱状图统计
- **用例库导入/导出** — ImportDialog（5 步向导）+ ExportDialog（多格式多范围）
- **知识库 4 分类** — 企业测试规范/业务领域知识/历史用例/技术参考
- **模板库双 Tab** — 用例结构模板 + Prompt 模板
- **回收站增强** — 到期倒计时颜色警告 + 清空回收站
- **设置页审计日志** — 操作日志查看 Tab
- **全局搜索增强** — Cmd+K 接入 searchApi，300ms 防抖
- **Diff 双 Tab** — 文本对比 + 变更摘要分离展示
- **新手引导系统** — 8 步流程引导模态框
- **文档模板** — CSV 用例导入模板 + Markdown 需求模板
- **共享组件** — FormDialog / FormField / TableSkeleton
- **数据模型增强** — TestCaseFolder（3 级目录）/ RecycleItem / PromptHistory

### Changed

- **RAG 相似度阈值** — 默认 score_threshold 从 0.3 提升至 0.72
- **文案标准化** — 「诊断」→「分析」全站替换，按钮文案「创建」→「新建」统一
- **版本号** — v0.2 → v2.0
- **错误处理** — 新增 getErrorMessage() 统一工具函数

### Removed

- AntdProvider 及所有 antd/@ant-design/icons 依赖
- 冗余菜单项：迭代测试计划 / 协作功能 / 独立覆盖度入口 / 独立诊断入口

---

### Added (prior)

- **M06 用例管理中心 — 目录树功能**：左侧 220px 固定目录树，支持层级展开/折叠；从 `module_path` 字段动态构建树；点击目录过滤右侧用例列表；特殊"未分类"节点显示 module_path 为空的用例
- **M06 用例管理中心 — StatCard 全量统计**：从 `/api/testcases/stats` 获取全量数据，修复原先仅统计当前页20条的问题
- **M06 CaseEditForm — 目录路径编辑**：编辑用例时可设置所属目录，支持 `/` 分隔多级路径
- **AI配置 — 通用提供商选择表单**：AI模型配置页面从硬编码3卡片改为动态表单；通过 `GET /api/ai-config/providers` 加载提供商列表（智谱AI/阿里云百炼/OpenAI）；3步式交互：选提供商→选模型版本→输入API Key

### Changed

- `backend/app/modules/testcases/service.py`：`list_cases()` 支持 `module_path` 过滤（精确+前缀匹配）；特殊值 `__uncategorized__` 过滤 NULL/空路径；新增 `get_module_paths()` 构建树形结构
- `backend/app/modules/testcases/router.py`：新增 `GET /api/testcases/module-paths` 端点
- `backend/app/modules/ai_config/router.py`：新增 `GET /api/ai-config/providers` 静态端点
- `frontend/src/app/(main)/testcases/_components/types.ts`：`TestCaseDetail` 新增 `module_path` 字段

### Added (Phase 0–5: Full Platform Implementation)

- **Progress Dashboard**: Visual FAB + Drawer showing real-time M00–M21 module completion status
  - `progress.json` tracking file with phase/module status
  - Next.js API route `/api/progress` serving live status
  - `ProgressDashboard.tsx` component with auto-refresh

- **Backend — All 18 modules now fully implemented** (router + service + models + schemas):
  - M00 `products/`: Full CRUD for products, iterations, requirements with auto-versioning
  - M03 `diagnosis/`: Health diagnosis with SSE streaming chat, report lifecycle, message history
  - M04 `scene_map/`: Test point generation via AI streaming, confirm/delete, grouped scene tree
  - M05 `generation/`: Multi-mode workbench sessions, SSE chat with test point context injection
  - M06 `testcases/`: Paginated CRUD, version snapshots, batch status updates, step management
  - M07 `diff/`: Myers algorithm text diff + impact analysis, affected test points/cases tracking
  - M08 `coverage/`: Requirement↔TestCase coverage matrix, iteration-level and product-level views
  - M09 `test_plan/`: Iteration test plan CRUD with status workflow
  - M10 `templates/`: Test case template library with usage tracking
  - M11 `knowledge/`: Knowledge base document CRUD with type filtering and versioning
  - M12 `export/`: JSON and CSV export of test cases with steps
  - M13 `execution/`: Execution result submission (single + batch), pass rate stats
  - M14 `analytics/`: Quality overview, priority/status/source distribution metrics
  - M16 `notification/`: Notification CRUD with read/unread tracking
  - M19 `dashboard/`: Stats, recent activities, product overview endpoints
  - M20 `audit/`: Audit log recording and paginated query
  - M21 `recycle/`: Soft-deleted item listing, restore, permanent delete
  - `auth/`: JWT authentication + bcrypt password hashing

- **Backend infrastructure**:
  - Dynamic router registration via `importlib` with graceful error handling (88 routes)
  - CORS wildcard origins for development
  - All models extend `BaseModel` with `SoftDeleteMixin` (deleted_at)

- **Frontend — All 12 pages connected to real backend APIs**:
  - Dashboard: Real-time stats, product overview, recent activities via React Query
  - Products: Full CRUD with Ant Design Table, search, modals
  - Iterations: CRUD filtered by product, date pickers, linked navigation
  - Requirements: Requirement cards with upload support
  - Diagnosis: 3-panel layout with requirement tree, SSE streaming chat, health score ring
  - Scene Map: 3-column layout with AI test point generation, confirm/delete, scene tree
  - Workbench: Multi-mode generation sessions, SSE streaming, test case sidebar
  - TestCases: Paginated table with filters, stats cards, search
  - Diff: Version comparison with impact analysis and change history
  - Coverage: Product/iteration coverage matrix with progress bars
  - Analytics: Quality dashboard with distribution charts
  - Knowledge: Document CRUD with type filtering
  - Templates: Template library with usage tracking and category filters

- **Frontend toolchain**: bun, Biome, TypeScript strict mode, next-themes dark/light/system
- **Infrastructure**: Docker Compose with PostgreSQL 16, Redis 7, Qdrant, MinIO
- **CI/CD**: GitHub Actions for backend + frontend + docs
- **Developer experience**: `init.sh`, `CLAUDE.md`, `.editorconfig`, `.env.example`
- **Documentation**: Requirements doc, development guide, implementation plans
