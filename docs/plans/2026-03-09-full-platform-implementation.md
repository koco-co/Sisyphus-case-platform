# Sisyphus Case Platform — 全模块实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 完整实现 Sisyphus Case Platform 的 M00-M21 全部 22 个业务模块，打通前后端数据流，对齐原型图 UI，构建可视化进度大盘。

**Architecture:** FastAPI DDD 后端 (21 模块 router/models/schemas/service) + Next.js 16 前端 (App Router + Ant Design + Tailwind + Zustand)。AI 流式通过 SSE 协议，ZhiPu GLM-4-Flash 作为默认模型。所有业务表使用 SoftDeleteMixin 软删除。

**Tech Stack:** Python 3.12 (uv) | FastAPI | SQLAlchemy 2.0 async | Alembic | Next.js 16 | React 19 | Ant Design 6 | Tailwind 4 | Zustand | React Query | ZhiPu AI SDK

---

## 现状分析

### 已实现（有真实逻辑）
- **M00 Products**: Product/Iteration/Requirement 模型 + CRUD + 文件上传
- **M03 Diagnosis**: DiagnosisReport/Risk/ChatMessage 模型 + 流式诊断
- **M04 Scene Map**: SceneMap/TestPoint 模型 + 流式生成
- **M05 Generation**: GenerationSession/Message 模型 + AI 对话流式
- **M06 TestCases**: TestCase/Step/Version 模型 + CRUD
- **Auth**: User 模型 + JWT 登录注册
- **AI Adapter**: ZhiPu/OpenAI/Anthropic 统一流式适配器
- **Shared**: BaseModel (UUID + Timestamps + SoftDelete) + enums

### 空壳/TODO 模块（仅有 stub router）
M01(UDA), M02(Import), M07(Diff), M08(Coverage), M09(TestPlan), M10(Templates), M11(Knowledge), M12(Export), M13(Execution), M14(Analytics), M16(Notification), M17(Search), M18(Collaboration), M19(Dashboard), M20(Audit), M21(Recycle)

### 前端状态
- 所有页面使用硬编码 demo 数据，未连接后端 API
- 主题切换（dark/light）已实现
- lucide-react 图标已替换 emoji
- SSE streaming hook 已实现

---

## Phase 0: 进度大盘 + 基础设施

### Task 0.1: 创建 progress.json 进度状态文件
**Files:**
- Create: `progress.json` (项目根目录)

进度文件记录所有模块和阶段的实现状态，前端可读取展示。

### Task 0.2: 前端进度大盘组件
**Files:**
- Create: `frontend/src/components/ui/ProgressDashboard.tsx`
- Modify: `frontend/src/app/(main)/layout.tsx` — 添加悬浮按钮入口

FAB 按钮 + Drawer 弹窗，展示 M00-M21 模块进度条/步骤树。

### Task 0.3: 进度 API 端点
**Files:**
- Modify: `backend/app/main.py` — 添加 GET /api/progress 端点

读取 progress.json 返回给前端。

**Commit:** `feat: ✨ 添加可视化进度大盘组件与API`

---

## Phase 1: 核心领域模型完善 (M00, M19)

### Task 1.1: Dashboard API — 首页仪表盘统计
**Files:**
- Modify: `backend/app/modules/dashboard/service.py`
- Modify: `backend/app/modules/dashboard/router.py`

实现统计接口：产品数、迭代数、用例总数、覆盖率、最近活动。

### Task 1.2: Products CRUD 完善 + 前端联调
**Files:**
- Modify: `backend/app/modules/products/router.py` — 补充 PATCH/DELETE
- Modify: `frontend/src/app/(main)/page.tsx` — 首页连接 dashboard API
- Modify: `frontend/src/app/(main)/products/page.tsx` — 连接 products API
- Modify: `frontend/src/app/(main)/iterations/page.tsx` — 连接 iterations API

### Task 1.3: Requirements 页面完善
**Files:**
- Modify: `frontend/src/app/(main)/requirements/page.tsx` — 完善需求卡片编辑器
- Create: `frontend/src/app/(main)/requirements/[id]/page.tsx` — 需求详情页

**Commit:** `feat: ✨ M00/M19 产品管理与仪表盘API联调`

---

## Phase 2: AI 诊断与场景地图 (M03, M04)

### Task 2.1: Diagnosis 后端完善
**Files:**
- Modify: `backend/app/modules/diagnosis/service.py` — 添加自动创建报告+风险解析
- Modify: `backend/app/modules/diagnosis/router.py` — 完善端点
- Modify: `backend/app/modules/diagnosis/schemas.py` — 补充请求/响应模型

诊断流程：触发诊断 → AI 流式返回 → 解析出 6 类风险 → 存入 DiagnosisReport/Risk。

### Task 2.2: Diagnosis 前端联调
**Files:**
- Modify: `frontend/src/app/(main)/diagnosis/page.tsx` — 连接后端 API
- Modify: `frontend/src/app/(main)/diagnosis/[id]/page.tsx` — 诊断详情

三栏布局：风险报告 | AI 对话 | 场景预览。

### Task 2.3: Scene Map 后端完善
**Files:**
- Modify: `backend/app/modules/scene_map/service.py` — AI 测试点解析
- Modify: `backend/app/modules/scene_map/router.py` — 确认/导出端点

测试点生成：流式生成 → 解析 JSON → 存入 TestPoint 表。

### Task 2.4: Scene Map 前端联调
**Files:**
- Modify: `frontend/src/app/(main)/scene-map/page.tsx` — 连接后端
- Modify: `frontend/src/app/(main)/scene-map/[id]/page.tsx` — 详情页

**Commit:** `feat: ✨ M03/M04 诊断与场景地图AI流式生成`

---

## Phase 3: 用例生成引擎与管理 (M05, M06)

### Task 3.1: Generation 工作台后端完善
**Files:**
- Modify: `backend/app/modules/generation/service.py` — AI 用例解析
- Modify: `backend/app/modules/generation/router.py` — 流式生成端点

四种生成模式：测试点驱动、文档驱动、对话引导、模板填充。

### Task 3.2: TestCases 管理完善
**Files:**
- Modify: `backend/app/modules/testcases/service.py` — 筛选/批量/版本
- Modify: `backend/app/modules/testcases/router.py` — 批量操作端点

### Task 3.3: Workbench 前端完善
**Files:**
- Modify: `frontend/src/app/(main)/workbench/page.tsx` — 完善三栏布局
- Modify: `frontend/src/app/(main)/workbench/[id]/page.tsx` — 详情页

### Task 3.4: TestCases 前端联调
**Files:**
- Modify: `frontend/src/app/(main)/testcases/page.tsx` — 连接后端 API

**Commit:** `feat: ✨ M05/M06 用例生成工作台与管理中心`

---

## Phase 4: Diff 引擎与覆盖矩阵 (M07, M08, M13)

### Task 4.1: Diff 模块后端实现
**Files:**
- Modify: `backend/app/modules/diff/models.py` — RequirementDiff 模型
- Create: `backend/app/modules/diff/schemas.py`
- Modify: `backend/app/modules/diff/service.py` — Myers + LLM 两阶段 Diff
- Modify: `backend/app/modules/diff/router.py`

### Task 4.2: Coverage 模块后端实现
**Files:**
- Modify: `backend/app/modules/coverage/models.py`
- Create: `backend/app/modules/coverage/schemas.py`
- Modify: `backend/app/modules/coverage/service.py` — 覆盖度矩阵计算
- Modify: `backend/app/modules/coverage/router.py`

### Task 4.3: Execution 回流模块
**Files:**
- Modify: `backend/app/modules/execution/models.py` — ExecutionResult 模型
- Create: `backend/app/modules/execution/schemas.py`
- Create: `backend/app/modules/execution/service.py`
- Modify: `backend/app/modules/execution/router.py`

### Task 4.4: Diff/Coverage 前端联调
**Files:**
- Modify: `frontend/src/app/(main)/diff/page.tsx` — 连接后端
- Modify: `frontend/src/app/(main)/coverage/page.tsx` — 覆盖度矩阵视图

**Commit:** `feat: ✨ M07/M08/M13 Diff引擎与覆盖度矩阵`

---

## Phase 5: 辅助模块 (M09-M12, M14-M21)

### Task 5.1: Templates 模块 (M10)
**Files:**
- Modify: `backend/app/modules/templates/models.py`
- Create: `backend/app/modules/templates/schemas.py`
- Modify: `backend/app/modules/templates/service.py`
- Modify: `backend/app/modules/templates/router.py`
- Modify: `frontend/src/app/(main)/templates/page.tsx`

### Task 5.2: Knowledge 模块 (M11)
**Files:**
- Modify: `backend/app/modules/knowledge/models.py`
- Create: `backend/app/modules/knowledge/schemas.py`
- Modify: `backend/app/modules/knowledge/service.py`
- Modify: `backend/app/modules/knowledge/router.py`
- Modify: `frontend/src/app/(main)/knowledge/page.tsx`

### Task 5.3: Analytics 看板 (M14)
**Files:**
- Modify: `backend/app/modules/analytics/service.py`
- Modify: `backend/app/modules/analytics/router.py`
- Modify: `frontend/src/app/(main)/analytics/page.tsx`

### Task 5.4: Audit 审计日志 (M20)
**Files:**
- Create: `backend/app/modules/audit/schemas.py`
- Create: `backend/app/modules/audit/service.py`
- Modify: `backend/app/modules/audit/router.py`

### Task 5.5: Recycle 回收站 (M21)
**Files:**
- Create: `backend/app/modules/recycle/models.py`
- Create: `backend/app/modules/recycle/schemas.py`
- Create: `backend/app/modules/recycle/service.py`
- Modify: `backend/app/modules/recycle/router.py`

### Task 5.6: 其他辅助模块 (M09, M12, M16, M17, M18)
**Files:**
- TestPlan (M09), Export (M12), Notification (M16), Search (M17), Collaboration (M18)
- 各模块 models/schemas/service/router

### Task 5.7: Settings 页面联调
**Files:**
- Modify: `frontend/src/app/(main)/settings/page.tsx`

**Commit:** `feat: ✨ M09-M21 辅助模块全量实现`

---

## Phase 6: UI 抛光与验收

### Task 6.1: 全页面 UI 对齐原型图
- 逐页核对 CSS、布局、交互
- 确保 dark/light 主题适配完整

### Task 6.2: 前后端集成测试
- 确保所有 API 端点可达
- 确保 SSE 流式输出正常

### Task 6.3: agent-browser E2E 验收
- 自动化浏览器测试主流程
- 截图保存最终状态

### Task 6.4: 更新文档
- 更新 CHANGELOG.md
- 更新 progress.json 为全部完成

**Commit:** `docs: 📝 更新 CHANGELOG 和进度大盘`

---

## 执行策略

1. 每个 Phase 完成后更新 progress.json + CHANGELOG.md
2. 使用 subagent-driven-development 并行执行独立模块
3. 后端模块优先，前端联调跟进
4. 每个 Commit 遵循 Conventional Commits + Gitmoji
