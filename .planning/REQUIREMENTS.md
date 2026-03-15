# Requirements: Sisyphus-Y 测试用例平台（2026-03 迭代）

**Defined:** 2026-03-15
**Core Value:** 让测试工程师专注测试策略——平台生成用例草稿，人负责决策

---

## v1 Requirements

### 分析台（M03 重构）

- [ ] **ANA-01**: 「诊断」全局重命名为「分析」（页面/按钮/API路由/注释/数据库字段注释）
- [ ] **ANA-02**: 分析台布局：左侧需求列表按迭代分组，每条需求显示状态 Badge（未分析/分析中/已完成）
- [ ] **ANA-03**: 右侧三 Tab 同页切换：需求详情 / AI 分析 / 覆盖追踪，切换不丢失状态
- [ ] **ANA-04**: AI 分析 Tab 内：上方广度扫描结果 + 下方苏格拉底追问对话框，上下布局
- [ ] **ANA-05**: 覆盖追踪 Tab：需求点 × 场景类型矩阵视图，展示当前用例覆盖情况
- [ ] **ANA-06**: 分析结果刷新后完整恢复（持久化到 DB）
- [ ] **ANA-07**: 存在未处理高风险遗漏项时「进入工作台」按钮置灰，hover 提示文案

### 工作台（M05 重构）

- [ ] **WRK-01**: 步骤条固定顶部，显示「Step 1 确认测试点 → Step 2 生成用例」，当前步骤高亮
- [ ] **WRK-02**: Step1 中栏：AI 生成测试点草稿，按场景类型分组，每条显示名称/Badge/预估用例数
- [ ] **WRK-03**: Step1 支持勾选/取消/手动添加测试点，至少勾选1个「开始生成」才激活
- [ ] **WRK-04**: Step1 右栏：已选测试点汇总 + RAG 检索历史用例预览（top-5，相似度≥0.72）
- [ ] **WRK-05**: Step2 中栏：SSE 流式输出 + AI 思考过程折叠块 + CaseCard 逐条渲染
- [ ] **WRK-06**: Step2 右栏：已生成用例列表，实时计数，按测试点分组
- [ ] **WRK-07**: Step2 完成后可点步骤条回到 Step1 补充测试点继续追加生成

### 历史用例清洗与 RAG（M02 + M11）

- [ ] **RAG-01**: 并行 subagent 调用 /functional-test-case-reviewer 审查「清洗后数据」目录下所有用例
- [ ] **RAG-02**: 审查规则：第一步必须是「进入[完整路径]页面」；每步有预期结果；前置条件含 SQL；步骤独立；预期可验证
- [ ] **RAG-03**: 审查通过→入向量库；可修复→润色后入库；无法修复→丢弃并记录原因
- [ ] **RAG-04**: 审查完成输出报告（总数/通过/润色/丢弃/丢弃原因汇总）
- [ ] **RAG-05**: RAG 检索 top-5，阈值 0.72，检索结果注入 Prompt 时带相似度分数
- [ ] **RAG-06**: 修复前端 SSE 内容中 `\n` 不转换为换行的渲染 bug
- [ ] **RAG-07**: 统一历史数据中英文字段名（全部改为中文：步骤/前置条件/预期结果等）
- [ ] **RAG-08**: 重新入向量库前先清空旧向量记录（避免重复向量）

### Prompt 体系重写（engine/ + ai/prompts.py）

- [ ] **PRM-01**: 全部6个模块 System Prompt 重写，四段式结构：身份声明/任务边界/输出规范/质量红线
- [ ] **PRM-02**: 各模块身份声明差异化，精准对应模块职责，禁止6个模块使用相同声明
- [ ] **PRM-03**: 在 Prompt 中注入 Few-shot 正例（正常/异常/边界三种）+ 负面示例
- [ ] **PRM-04**: 智谱主力模型切换为 `glm-5`

### 需求录入优化（M00 + M01）

- [ ] **INP-01**: 上传需求入口旁添加「下载模板」按钮，提供 docx/md 格式（放 public/templates/）
- [ ] **INP-02**: UDA 解析后按章节/功能点自动拆分为独立需求条目，用户确认结构后保存
- [ ] **INP-03**: 非标准文档给出「识别置信度较低」提示，不阻断，用户可选择继续

### 用例库增强（M06）

- [ ] **TC-01**: 三级目录树：产品/迭代/需求自动归属，超过3层置灰提示
- [ ] **TC-02**: 目录双击重命名（回车确认/Esc取消），不能为空/重名，超20字截断
- [ ] **TC-03**: 目录删除：有用例时二次确认弹窗，确认后目录和用例全入回收站；空目录直接删
- [ ] **TC-04**: 同级目录拖拽排序（持久化），跨层级通过右键「移动到…」实现
- [ ] **TC-05**: 拖拽用例到不同目录（单条或多选批量），同时支持右键「移动到…」
- [ ] **TC-06**: 「未分类」目录不可删除/重命名，所有无指定目录的用例自动归入
- [ ] **TC-07**: 导入支持 xlsx/csv/json/xmind 四种格式，提供对应模板下载
- [ ] **TC-08**: 非标准文件上传时进入字段映射步骤，必填字段未映射则禁止导入
- [ ] **TC-09**: 导入必有预览步骤（前5条解析结果），用户确认后才正式导入
- [ ] **TC-10**: 重复检测（标题+目录唯一），预览步骤列出重复条目，用户选覆盖/跳过/重命名导入
- [ ] **TC-11**: 导入完成 Toast：「成功导入 N 条，跳过 M 条，覆盖 K 条」
- [ ] **TC-12**: 导出支持 xlsx/csv/xmind/md 四种格式
- [ ] **TC-13**: 导出范围：当前目录/按需求/按迭代/自由勾选（四种）
- [ ] **TC-14**: 导出自定义字段（复选框选择，XMind 格式固定全字段）

### 知识库增强（M11）

- [ ] **KB-01**: 四固定分类：企业测试规范/业务领域知识/历史用例/技术参考
- [ ] **KB-02**: 文档分块预览抽屉（序号/token数/内容），支持删除单个 chunk
- [ ] **KB-03**: 手动添加知识条目（标题/分类/内容/标签），直接向量化入库，显示「手动」Badge
- [ ] **KB-04**: 文档版本管理：新版本上传弹确认，旧版本停用不参与检索，最多保留3版，超限自动删除最旧

### 仪表盘重构（M19）

- [ ] **DSH-01**: 顶部4卡片：需求总数/用例总数/平均覆盖率/本迭代进度，含与上迭代 delta
- [ ] **DSH-02**: 中部折线图：近6迭代用例总量/P0覆盖率/缺陷发现率，三线可单独显示
- [ ] **DSH-03**: 中部环形图：当前迭代用例来源占比（AI生成/历史导入/手动创建）
- [ ] **DSH-04**: 底部：最近5条需求动态 + 待处理事项列表（高风险/需重写/低覆盖率，含「去处理」跳转）
- [ ] **DSH-05**: 右上角迭代选择器，切换后所有图表同步更新
- [ ] **DSH-06**: 「质量分析」Tab：迭代用例质量分布 + AI 生成效率统计

### UI 规范与体验（全局）

- [ ] **UX-01**: 按钮文案统一「新建 + 对象名」，全局搜索消除「新增」「创建」（上传/添加/导入保留）
- [ ] **UX-02**: 简单删除弹窗：「确定删除「xxx」？删除后可在回收站中找回。」
- [ ] **UX-03**: 级联删除弹窗：显示影响范围（N条用例），危险按钮用 sy-danger
- [ ] **UX-04**: 空状态页面：图标48px + 暂无文案 + 引导操作按钮，零空白页，搜索无结果不显示新建按钮
- [ ] **UX-05**: 列表首次加载用骨架屏，按钮操作用 Loader2，路由跳转用 nprogress，弹窗内用 Spinner
- [ ] **UX-06**: 首次登录全屏引导弹窗（核心流程图），只弹一次，底部「跳过」和「下一步」
- [ ] **UX-07**: 右下角固定「?」帮助浮动按钮（sy-accent + HelpCircle + bottom-6 right-6）
- [ ] **UX-08**: AI 未配置时分析台/工作台顶部显示固定警告横幅，含「前往配置」跳转

### 需求 Diff（M07）

- [ ] **DIF-01**: 「发布新版本」按钮在需求编辑器右上角，点击填写版本说明（选填）后触发 Diff
- [ ] **DIF-02**: 文本对比 Tab：左旧右新，删除红/新增绿/修改黄，支持折叠未变更段落
- [ ] **DIF-03**: 变更摘要 Tab：卡片列表，每卡显示变更类型+摘要+业务影响
- [ ] **DIF-04**: Diff 后自动影响分析，受影响用例打标（需重写/需复核/不受影响）
- [ ] **DIF-05**: 「一键推送到工作台」将「需重写」用例批量推送，用例列表同步显示对应 Badge

### 模块裁剪

- [x] **MOD-01**: M09 迭代测试计划：删除前端入口和后端路由（保留DB表）
- [x] **MOD-02**: M18 协作功能：删除前端入口，后端保留但不注册路由
- [ ] **MOD-03**: M16 通知：简化为 Toast + 长任务进度条，不做通知中心和消息列表
- [ ] **MOD-04**: M17 全局搜索：Cmd+K 唤起，只搜用例（标题+步骤）和需求（标题+内容），结果按类型分组
- [ ] **MOD-05**: M20 操作日志：设置页只读列表（最近100条，时间范围筛选）

### 回收站与模板库

- [ ] **REC-01**: 回收站30天自动清理，到期前3天标红，支持手动清空（二次确认）
- [ ] **REC-02**: 回收站 Tab 筛选：全部/需求/用例/知识库文档
- [ ] **REC-03**: 恢复时原目录不存在则移入「未分类」，支持批量恢复并 Toast 汇总
- [ ] **TPL-01**: 模板库双 Tab：Prompt 模板（适用模块/内容/备注）+ 用例结构模板（场景类型/步骤模板/占位符）
- [ ] **TPL-02**: 内置数据中台场景默认模板（只读「内置」Badge），可复制后另存
- [ ] **TPL-03**: 模板导出/导入 JSON

---

## v2 Requirements（本迭代不做）

- M13 执行结果回流（TestRail 对接）
- 前端 E2E 自动化（Playwright）
- 模板市场/在线分享
- 多人协作实时编辑

---

## Out of Scope

| 功能 | 原因 |
|------|------|
| M09 迭代测试计划 | 工作台已覆盖，删除 |
| M18 协作编辑 | 实现复杂度极高 |
| M13 执行回流 | 独立集成周期，暂缓 |
| XMind zen 版本 | 只验证 xmind2026 |
| PDF 导出 | 结构化内容体验差 |
| Excel 自定义模板样式 | 频率低 |
| 通知中心/消息列表 | 只做 Toast |
| 质量看板独立菜单 | 合并入仪表盘 Tab |

---

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| MOD-01 | Phase 1 | Complete |
| MOD-02 | Phase 1 | Complete |
| MOD-03 | Phase 1 | Pending |
| MOD-04 | Phase 1 | Pending |
| MOD-05 | Phase 1 | Pending |
| ANA-01 | Phase 2 | Pending |
| ANA-02 | Phase 2 | Pending |
| ANA-03 | Phase 2 | Pending |
| ANA-04 | Phase 2 | Pending |
| ANA-05 | Phase 2 | Pending |
| ANA-06 | Phase 2 | Pending |
| ANA-07 | Phase 2 | Pending |
| WRK-01 | Phase 2 | Pending |
| WRK-02 | Phase 2 | Pending |
| WRK-03 | Phase 2 | Pending |
| WRK-04 | Phase 2 | Pending |
| WRK-05 | Phase 2 | Pending |
| WRK-06 | Phase 2 | Pending |
| WRK-07 | Phase 2 | Pending |
| RAG-01 | Phase 3 | Pending |
| RAG-02 | Phase 3 | Pending |
| RAG-03 | Phase 3 | Pending |
| RAG-04 | Phase 3 | Pending |
| RAG-05 | Phase 3 | Pending |
| RAG-06 | Phase 3 | Pending |
| RAG-07 | Phase 3 | Pending |
| RAG-08 | Phase 3 | Pending |
| PRM-01 | Phase 3 | Pending |
| PRM-02 | Phase 3 | Pending |
| PRM-03 | Phase 3 | Pending |
| PRM-04 | Phase 3 | Pending |
| INP-01 | Phase 4 | Pending |
| INP-02 | Phase 4 | Pending |
| INP-03 | Phase 4 | Pending |
| TC-01 | Phase 4 | Pending |
| TC-02 | Phase 4 | Pending |
| TC-03 | Phase 4 | Pending |
| TC-04 | Phase 4 | Pending |
| TC-05 | Phase 4 | Pending |
| TC-06 | Phase 4 | Pending |
| TC-07 | Phase 4 | Pending |
| TC-08 | Phase 4 | Pending |
| TC-09 | Phase 4 | Pending |
| TC-10 | Phase 4 | Pending |
| TC-11 | Phase 4 | Pending |
| TC-12 | Phase 4 | Pending |
| TC-13 | Phase 4 | Pending |
| TC-14 | Phase 4 | Pending |
| DSH-01 | Phase 4 | Pending |
| DSH-02 | Phase 4 | Pending |
| DSH-03 | Phase 4 | Pending |
| DSH-04 | Phase 4 | Pending |
| DSH-05 | Phase 4 | Pending |
| DSH-06 | Phase 4 | Pending |
| DIF-01 | Phase 4 | Pending |
| DIF-02 | Phase 4 | Pending |
| DIF-03 | Phase 4 | Pending |
| DIF-04 | Phase 4 | Pending |
| DIF-05 | Phase 4 | Pending |
| KB-01 | Phase 4 | Pending |
| KB-02 | Phase 4 | Pending |
| KB-03 | Phase 4 | Pending |
| KB-04 | Phase 4 | Pending |
| UX-01 | Phase 5 | Pending |
| UX-02 | Phase 5 | Pending |
| UX-03 | Phase 5 | Pending |
| UX-04 | Phase 5 | Pending |
| UX-05 | Phase 5 | Pending |
| UX-06 | Phase 5 | Pending |
| UX-07 | Phase 5 | Pending |
| UX-08 | Phase 5 | Pending |
| REC-01 | Phase 5 | Pending |
| REC-02 | Phase 5 | Pending |
| REC-03 | Phase 5 | Pending |
| TPL-01 | Phase 5 | Pending |
| TPL-02 | Phase 5 | Pending |
| TPL-03 | Phase 5 | Pending |

**Coverage:**
- v1 requirements: 68 total
- Mapped to phases: 68
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-15*
*Last updated: 2026-03-15 — Traceability updated after roadmap finalized (5-phase structure)*
