# Roadmap: Sisyphus-Y 测试用例平台（2026-03 迭代）

## Overview

本迭代从清理冗余模块入手，重建核心主链路（分析台 → 工作台），再提升 AI 质量（RAG 历史用例清洗 + Prompt 重写），然后扩展外围能力（用例库/仪表盘/Diff），最终以全局体验打磨收尾。每个 Phase 交付一个可验证的完整能力集。

## Phases

- [ ] **Phase 1: 清场** - 裁剪废弃模块，为主链路重构扫清路由冲突和 UI 噪声
- [ ] **Phase 2: 主链路重构** - 分析台三 Tab 布局 + 工作台步骤条，核心流程端到端跑通
- [ ] **Phase 3: AI 质量提升** - 历史用例审查入向量库 + Prompt 体系重写 + GLM-5 切换
- [ ] **Phase 4: 外围模块扩展** - 需求录入优化、用例库完整能力、仪表盘重构、需求 Diff
- [ ] **Phase 5: 体验收尾** - 全局 UI 规范统一、回收站、模板库、知识库增强

## Phase Details

### Phase 1: 清场
**Goal**: 裁剪所有废弃/简化模块，让主链路重构在干净的代码库上展开
**Depends on**: Nothing (first phase)
**Requirements**: MOD-01, MOD-02, MOD-03, MOD-04, MOD-05
**Success Criteria** (what must be TRUE):
  1. 导航栏中 M09 迭代测试计划入口不可见，后端路由访问返回 404
  2. M18 协作功能入口从前端消失，后端路由不注册（不影响 DB 表）
  3. 所有通知提示以 Toast + 进度条呈现，不存在通知中心/消息列表页面
  4. Cmd+K 唤起全局搜索，结果仅限用例和需求两类，按类型分组展示
  5. 设置页操作日志只读列表可正常加载最近 100 条，支持时间范围筛选
**Plans**: 3 plans

Plans:
- [ ] 01-01-PLAN.md — 裁剪 M09/M18 后端路由 + 删除前端 review 页面（MOD-01, MOD-02）
- [ ] 01-02-PLAN.md — 简化 M16 通知：注销后端路由 + 删除通知中心组件和页面（MOD-03）
- [ ] 01-03-PLAN.md — 裁剪全局搜索为2类 + 补完审计日志时间筛选（MOD-04, MOD-05）

### Phase 2: 主链路重构
**Goal**: 分析台和工作台完成重构，测试工程师可无中断地完成「分析需求 → 确认测试点 → 生成用例」全流程
**Depends on**: Phase 1
**Requirements**: ANA-01, ANA-02, ANA-03, ANA-04, ANA-05, ANA-06, ANA-07, WRK-01, WRK-02, WRK-03, WRK-04, WRK-05, WRK-06, WRK-07
**Success Criteria** (what must be TRUE):
  1. 分析台页面所有「诊断」字样已替换为「分析」，包括按钮、路由、日志
  2. 分析台左侧需求列表按迭代分组，每条需求显示状态 Badge；右侧三 Tab（需求详情/AI 分析/覆盖追踪）切换不刷新，刷新后状态完整恢复
  3. AI 分析 Tab 内广度扫描结果在上、苏格拉底追问对话框在下，两区同屏可见
  4. 存在未处理高风险项时「进入工作台」按钮置灰，hover 显示提示文案
  5. 工作台步骤条固定顶部，Step1 可勾选/手动添加测试点并预览 RAG 历史用例，Step2 SSE 流式输出用例，完成后可回到 Step1 补充再生成
**Plans**: TBD

### Phase 3: AI 质量提升
**Goal**: 向量库中存储经过审查的高质量历史用例，所有 AI 模块使用重写后的 Prompt，RAG 检索结果可信
**Depends on**: Phase 2
**Requirements**: RAG-01, RAG-02, RAG-03, RAG-04, RAG-05, RAG-06, RAG-07, RAG-08, PRM-01, PRM-02, PRM-03, PRM-04
**Success Criteria** (what must be TRUE):
  1. 历史用例审查完成后可查看报告（通过/润色/丢弃数量及丢弃原因汇总）
  2. 工作台 Step1 右栏 RAG 历史用例预览显示 top-5 结果，每条附相似度分数，且分数 ≥ 0.72
  3. SSE 流式输出中换行符正确渲染为换行（而非显示 `\n` 字符）
  4. 设置页模型配置中可选择 `glm-5`，选择后 AI 分析和工作台均使用新模型
  5. 各 AI 模块使用差异化身份声明的 Prompt，含 Few-shot 正负例，输出结构稳定
**Plans**: TBD

### Phase 4: 外围模块扩展
**Goal**: 需求录入更智能、用例库拥有完整目录管理和导入导出、仪表盘数据驱动决策、需求 Diff 支持变更影响分析
**Depends on**: Phase 2
**Requirements**: INP-01, INP-02, INP-03, TC-01, TC-02, TC-03, TC-04, TC-05, TC-06, TC-07, TC-08, TC-09, TC-10, TC-11, TC-12, TC-13, TC-14, DSH-01, DSH-02, DSH-03, DSH-04, DSH-05, DSH-06, DIF-01, DIF-02, DIF-03, DIF-04, DIF-05, KB-01, KB-02, KB-03, KB-04
**Success Criteria** (what must be TRUE):
  1. 上传需求入口旁「下载模板」按钮可用，UDA 解析后自动拆分条目并由用户确认再保存；非标准文档显示置信度提示但不阻断
  2. 用例库目录树支持双击重命名、拖拽排序、跨层级移动、删除级联确认，「未分类」目录受保护
  3. 导入流程完整走通（格式选择 → 字段映射 → 预览 → 重复处理 → 确认 → Toast 汇总），导出支持 4 种格式和 4 种范围
  4. 仪表盘顶部 4 卡片、折线图、环形图、待处理事项列表均正常渲染，迭代选择器切换后全局同步
  5. 「发布新版本」触发 Diff，文本对比 Tab 和变更摘要 Tab 均可用，受影响用例自动打标，可一键推送到工作台
  6. 知识库支持四固定分类、分块预览、手动添加条目、文档版本管理（最多3版）
**Plans**: TBD

### Phase 5: 体验收尾
**Goal**: 全平台 UI 规范统一、回收站软删除链路完整、模板库可用，整体体验无明显缺陷
**Depends on**: Phase 4
**Requirements**: UX-01, UX-02, UX-03, UX-04, UX-05, UX-06, UX-07, UX-08, REC-01, REC-02, REC-03, TPL-01, TPL-02, TPL-03
**Success Criteria** (what must be TRUE):
  1. 全平台按钮文案统一「新建 + 对象名」，删除弹窗使用规范模板（简单/级联两种），空状态页面零空白
  2. 列表首次加载显示骨架屏，按钮操作显示 Loader2，路由跳转有 nprogress 进度条
  3. 首次访问平台弹出全屏引导弹窗（只弹一次），右下角「?」帮助浮动按钮常驻
  4. AI 未配置时分析台/工作台顶部显示固定警告横幅，含「前往配置」跳转链接
  5. 回收站支持 Tab 筛选、批量恢复、30天自动清理提示；模板库支持内置模板只读预览、复制另存、JSON 导出导入
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in order: 1 → 2 → 3 → 4 → 5
(Phase 3 can partially overlap Phase 4 if RAG work is done in parallel)

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. 清场 | 2/3 | In Progress|  |
| 2. 主链路重构 | 0/TBD | Not started | - |
| 3. AI 质量提升 | 0/TBD | Not started | - |
| 4. 外围模块扩展 | 0/TBD | Not started | - |
| 5. 体验收尾 | 0/TBD | Not started | - |
