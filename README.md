<div align="center">

# 🧪 Sisyphus-case-platform

**AI 驱动的企业级功能测试用例自动生成平台**

*专为数据中台、数据湖仓、实时计算等复杂企业系统设计*

[![Version](https://img.shields.io/badge/version-v2.0.0--rc-blue.svg)](https://github.com/koco-co/Sisyphus-case-platform)
[![License](https://img.shields.io/badge/license-Enterprise-orange.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12+-3776AB.svg?logo=python&logoColor=white)](https://python.org)
[![Next.js](https://img.shields.io/badge/Next.js-16+-000000.svg?logo=next.js)](https://nextjs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![LangChain](https://img.shields.io/badge/LangChain-latest-1C3C3C.svg)](https://langchain.com)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

<br/>

> 💡 **核心理念**：测试用例生成分为两个本质不同的决策：**「测什么」**（测试点/场景地图）和**「怎么测」**（用例步骤）。Sisyphus-case-platform 显式拆分这两个阶段，通过「需求分析 → 测试点分析确认 → 约束式用例生成 → 变更影响追踪 → 执行回流」形成持续进化的质量飞轮。

<br/>

[📖 产品概述](#-产品概述) · [🗺 核心流程](#-核心生成流程) · [✨ 需求分析](#-需求分析系统) · [🎯 测试点分析](#-测试点分析--场景地图确认) · [📄 需求Diff](#-需求文档-diff--变更影响分析) · [🚀 快速开始](#-快速开始)

</div>

---

## 📋 目录

- [产品概述](#-产品概述)
- [功能模块总览](#-功能模块总览)
- [系统架构](#-系统架构)
- [UDA 内容抽象层](#-uda--universal-document-abstraction-层)
- [子产品 · 迭代 · 需求三级结构](#-子产品--迭代--需求三级层级结构)
- [需求录入：Requirement Card 编辑器](#-需求录入requirement-card-编辑器)
- [历史数据导入与清洗](#-历史数据导入与清洗)
- [核心生成流程](#-核心生成流程)
- [需求分析系统](#-需求分析系统)
- [测试点分析 & 场景地图确认](#-测试点分析--场景地图确认)
- [对话式生成工作台](#-对话式生成工作台)
- [需求文档 Diff & 变更影响分析](#-需求文档-diff--变更影响分析)
- [需求覆盖度矩阵](#-需求覆盖度矩阵)
- [执行结果回流 & 闭环飞轮](#-执行结果回流--闭环飞轮)
- [技术栈](#-技术栈)
- [数据模型](#-数据模型)
- [API 设计](#-api-设计)
- [开发路线图](#-开发路线图)
- [快速开始](#-快速开始)

---

## 🎯 产品概述

Sisyphus-case-platform 是一款面向**企业数据中台场景**的 AI 功能测试用例智能生成平台，支持子产品多迭代并行研发模式，覆盖从需求录入、需求分析、测试点分析、用例生成、变更追踪到执行回流的完整测试生命周期。

### 核心痛点对照表

| 挑战 | 传统方式 | Sisyphus-case-platform |
|---|---|---|
| 需求散乱、格式各异 | 人工整合成大文档，耗时数天 | Requirement Card + 平台自动聚合 |
| 覆盖方向错了才发现 | 写完几十条用例才发现测错了方向 | **测试点显式评审**，先对齐"测什么"再生成 |
| 需求遗漏场景多 | 依赖个人经验，上线后才发现 | AI 主动诊断 + 苏格拉底式场景补全 |
| 需求变更影响不清 | 人工地毯式排查，极易遗漏 | Diff 引擎 + 用例影响自动标记 |
| 通用 AI 生成质量差 | 结果需大量二次修改 | RAG + 行业知识库 + 约束式生成 |
| 历史数据格式混乱 | 无法复用，每轮从头写 | 智能导入清洗 + 向量化历史用例库 |
| 跨迭代知识不传承 | 经验断层，质量无法累积 | 执行结果回流 + 持续学习飞轮 |

### 目标效果

- ⚡ 单模块用例生成时间：**天级 → 小时级**（效率提升 70%+）
- 🎯 场景覆盖率：**达到人工编写的 90% 以上**
- 🔁 测试点评审通过后再生成：**大幅减少返工率**（方向错误在前期拦截）
- 🔍 需求变更影响：**秒级定位**受影响用例
- 📈 跨迭代质量提升：执行结果回流，每轮生成质量持续优化

## 🧭 2026-03 调整方向

本仓库当前处于“**能力已铺开，主链路再收敛**”的阶段。很多能力已经落地，但这不代表本轮改版已经完成。当前代码基线与本轮改版重点如下：

| 类别 | 当前已落地 | 本轮重点 |
| --- | --- | --- |
| 导航与信息架构 | 9 个一级菜单、仪表盘双 Tab、分析域入口、设置页 Prompt 管理 | 收敛分析域旧路由、消除重复页面心智 |
| 工作台 | 已有 SSE 生成、会话持久化、右侧用例列表 | 改为 `Step 1 确认测试点` → `Step 2 生成用例` 的同页流程 |
| AI 配置 | `glm-5`、provider 列表、Prompt 历史、默认值/回滚 | 让“模型列表 / 生效配置 / Prompt 管理”前后端体验完全一致 |
| 历史数据与 RAG | XMind 导入、目录树、RAG top-k=5、阈值 0.72 | 串起“清洗 → 审查 → 润色 → 重建向量 → 报告”的闭环 |

> 说明：
>
> - `process.json`：本轮前瞻性开发计划与执行状态。
> - `progress.json`：验收/回归任务记录与证据，不再承担开发计划职责。

---

## 📦 功能模块总览

| 模块 | 名称 | 核心能力 | 状态 |
|---|---|---|---|
| **M00** | 子产品/迭代/需求管理 | 三级层级结构，迭代周期管理，需求卡片编辑器 | `已实现` |
| **M01** | 文档解析引擎（UDA层） | 任意格式→内部AST，外链图片归档，统一结构化 | `已实现` |
| **M02** | 历史数据导入与清洗 | CSV/MD批量导入，AI清洗+人工审核，导入健康报告 | `已实现` |
| **M03** | 需求分析 | 6类遗漏识别，三层多轮追问，需求详情 / AI分析 / 覆盖追踪三 Tab | `已实现（正收敛到分析域）` |
| **M04** | 测试点分析 & 场景地图确认 | AI生成测试点草稿，粒度校验，用户评审确认，与场景地图统一 | `已实现（将复用到工作台 Step 1）` |
| **M05** | 对话式生成工作台 | SSE 流式输出、会话持久化、用例侧栏；正在重构为双步骤工作台 | `重构中` |
| **M06** | 用例管理中心 | CRUD、版本管理、3级目录树、多格式导入导出 | `已实现` |
| **M07** | 需求文档 Diff & 影响分析 | 版本对比（文本+语义双Tab），变更范围识别，受影响用例自动标记 | `已实现` |
| **M08** | 需求覆盖度矩阵 | 需求×用例二维视图，一眼发现覆盖空洞 | `已实现` |
| ~~M09~~ | ~~迭代测试计划生成~~ | ~~基于迭代需求自动草拟计划~~ | `已裁剪` |
| **M10** | 用例模板库 | 用例结构模板 + Prompt模板，双Tab管理 | `已实现` |
| **M11** | 知识库管理 | 4分类文档管理（企业规范/业务知识/历史用例/技术参考），RAG检索 | `已实现` |
| **M12** | 用例导出与集成 | Excel/CSV/XMind/JSON 多格式导出 | `已实现` |
| ~~M13~~ | ~~执行结果回流~~ | ~~失败/高质量用例标记~~ | `已推迟` |
| **M14→M19** | 质量分析看板 | 已合并至仪表盘质量分析Tab | `已合并` |
| **M16** | 通知系统 | 站内通知（简化版） | `已实现` |
| **M17** | 全局搜索 | Cmd+K 全局搜索，300ms防抖，API集成 | `已实现` |
| ~~M18~~ | ~~协作功能~~ | ~~评论、@提及~~ | `已裁剪` |
| **M19** | 首页仪表盘 | 项目概览 + 质量分析双Tab，支持迭代选择、上一迭代 delta 对比与按迭代统计 | `已实现` |
| **M20** | 操作审计日志 | 全局操作记录（集成至设置页） | `已实现` |
| **M21** | 回收站 | 软删除、30天自动清理、到期倒计时警告 | `已实现` |

---

## 🏗 系统架构

```
┌──────────────────────────────────────────────────────────────────────┐
│                  接入层：Nginx (反向代理 + 限流 + SSL) + CDN           │
└─────────────────────────────┬────────────────────────────────────────┘
                              │
┌─────────────────────────────▼────────────────────────────────────────┐
│                        前端层 (Next.js 16)                            │
│  仪表盘    │  分析台    │  工作台    │  需求Diff   │  用例库          │
│  模板库     │  知识库    │  回收站    │  设置       │                  │
└─────────────────────────────┬────────────────────────────────────────┘
                              │ REST / SSE / WebSocket
┌─────────────────────────────▼────────────────────────────────────────┐
│                          API 层 (FastAPI)                             │
│  需求服务  │  UDA解析  │  诊断服务  │  测试点服务  │  生成服务  │  用例服务 │
└──────┬──────────────────────┬─────────────────────┬───────────────────┘
       │                      │                     │
┌──────▼────────┐  ┌──────────▼──────────┐  ┌──────▼───────────────────┐
│  任务队列      │  │     AI 引擎层        │  │       存储层              │
│  (Celery      │  │  LangChain/Graph    │  │  PostgreSQL  (业务数据)   │
│   + Redis)    │  │  Prompt 管理        │  │  Redis       (缓存/队列)  │
│               │  │  多模型路由          │  │  Qdrant      (向量库)    │
│  文档解析      │  │  RAG 检索           │  │  MinIO       (文件归档)  │
│  Diff 计算     │  │  Diff 语义分析      │  └──────────────────────────┘
│  诊断扫描      │  │  粒度校验           │
│  图片归档      │  └─────────────────────┘
└───────────────┘
```

---

## 🔄 UDA — Universal Document Abstraction 层

> **核心原则**：平台内部永远不存原始文件格式，只存结构化内容。格式处理只发生在输入层和输出层。

```
任何格式输入               内部统一数据模型 (AST)           任何格式输出
──────────────            ──────────────────────          ─────────────
.docx        ──┐          ┌──────────────────┐            → .md
.pdf         ──┤          │  DocumentNode    │            → .docx
.md          ──┤  解析层→  │  ├ metadata      │  渲染层──→  → .pdf
.csv         ──┤          │  ├ sections[]     │            → .xlsx
图片(本地)   ──┤          │  │  ├ text         │            → XMind
网络图片URL  ──┤          │  │  ├ images[]     │            → Jira/Xray
Confluence链接 ┘          │  └ rules[]        │
                          └──────────────────┘
```

### 输入层处理规则

| 输入类型 | 解析方式 | 特殊处理 |
|---|---|---|
| `.docx / .doc` | python-docx | 保留标题层级、表格、列表 |
| `.pdf`（文本版） | pdfplumber | 保留段落结构、页码映射 |
| `.pdf`（扫描版） | PaddleOCR | 置信度<0.8时标记人工复核 |
| `.md` | Marked.js | 提取 frontmatter YAML + 章节树 |
| `.xlsx / .csv` | OpenPyXL / pandas | 字段映射 + 枚举值提取 |
| 图片（本地） | PaddleOCR + GPT-4 Vision | 识别流程图节点、界面标注 |
| **网络图片 URL** | **主动抓取→存MinIO→OCR** | **替换内部URL，防外链失效** |
| Confluence/飞书链接 | 调用对应 API | 需配置企业系统 Token |

### 导出格式矩阵

| 导出对象 | 支持格式 |
|---|---|
| 需求文档 | `.md` / `.docx` / `.pdf` |
| 测试用例集 | `.xlsx` / `.md` / `.docx` / `.pdf` / XMind |
| 测试点 & 场景地图 | `.png`（可视化）/ `.md`（结构列表）/ `.json` |
| 需求健康报告 | `.pdf` / `.md` |
| 迭代测试计划 | `.docx` / `.pdf` |
| 需求覆盖度矩阵 | `.xlsx` / `.png` |
| Diff 报告 | `.md` / `.html`（带高亮） |

---

## 🏢 子产品 · 迭代 · 需求三级层级结构

```
Platform
  └── 子产品（离线开发 / 实时开发 / 数据资产 / 数据治理 / BI分析...）
        └── 迭代（2025-Q2-Sprint3）
              └── 需求（REQ-OFFLINE-089，约1页PRD）
                    ├── 测试点列表（场景地图节点）
                    ├── 关联用例列表（可溯源到测试点）
                    └── 变更历史（Diff记录）
```

**为什么用三级结构而不是"整合成大文档"：**

| 维度 | 大文档方式 | 三级结构方式 |
|---|---|---|
| 录入成本 | 需人工整合，格式不统一 | 一页PRD即一张卡片，独立录入 |
| 测试点粒度 | 大文档测试点容易混淆 | 每条需求独立生成测试点，粒度清晰 |
| 变更追踪 | 无法定位到单条需求 | Diff 精准到需求节点级别 |
| AI 生成 | 大文档超出上下文窗口 | 按迭代自动聚合，智能分组送入 |

---

## 📝 需求录入：Requirement Card 编辑器

> 交互上像 Notion 块编辑器，底层存 Markdown + YAML frontmatter。

```markdown
---
product: 离线开发
iteration: 2025-Q2-Sprint3
requirement_id: REQ-OFFLINE-089
title: 数据开发任务草稿自动保存
author: 李明
status: confirmed
priority: P1
version: 1.2
tags: [自动保存, 草稿, 任务编辑]
---

## 功能描述
数据开发任务支持草稿自动保存，编辑器每隔 30 秒触发一次...

## 验收标准
- 编辑超过 30 秒未手动保存，系统自动保存草稿
- 草稿保存失败时右上角显示红色警告图标

## 相关资料
![任务编辑界面](https://internal.confluence.com/xxx)  ← 平台自动归档到MinIO
![草稿保存流程图](https://lucidchart.com/xxx)         ← 自动归档 + OCR提取文字
```

| 编辑器功能 | 说明 |
|---|---|
| 块编辑 | `/` 唤起：标题/列表/表格/图片/分割线 |
| 图片粘贴 | 粘贴截图自动上传归档，替换为内部 URL |
| AI 辅助补全 | 输入功能描述后，AI 辅助生成验收标准草稿 |
| 版本快照 | 每次"确认需求"自动创建版本快照，用于 Diff |
| 关联跳转 | 卡片内直接查看测试点列表和关联用例 |

---

## 🧹 历史数据导入与清洗

### 双轨处理策略

```
导入文件（CSV历史用例 / MD历史文档 / Word / PDF）
  │
  ├── [底层静默处理] 字段映射 / 图片归档 / 基础去重 / 空值填充 / 向量化
  │
  └── [导入健康报告] 展示需要人工决策的部分

✅ 自动处理成功   892 条  (72%)
⚠️ 需要人工确认  298 条  (24%)  ← AI做决策，人做审核，不需要配置规则
❌ 无法解析        50 条   (4%)
```

**人工确认类型：**

| 情况 | 处理方式 |
|---|---|
| 字段语义模糊（"测试点"是标题还是步骤？） | 展示两种解析结果，用户选择 |
| 图片 URL 已失效（404） | 标记"图片丢失"，支持用户重新上传 |
| 步骤全部塞在一个单元格 | AI 拆分结果 + 原始内容并排，用户确认 |
| 优先级值非标准（"重要"/"紧急"） | 展示映射关系，用户确认 |
| 疑似重复（标题相似度 > 85%） | 并排展示，用户选择合并/保留/删除 |

---

## 🚀 核心生成流程

> 这是整个平台最核心的设计——显式拆分「测什么」和「怎么测」两个决策，在对的时机做对的事。

```
需求卡片确认
      │
      ▼
① 🔍 需求分析
   识别6类遗漏风险 → 需求分析报告
      │
      ▼
② 💬 场景补全对话（苏格拉底模式）
   AI主动追问 → 用户确认/补充遗漏场景
      │
      ▼
③ 🎯 测试点分析 & 场景地图确认  ← 【关键评审节点】
   AI生成测试点草稿（即场景地图节点）
   用户在此增删改，与PM/业务方对齐覆盖范围
   确认后：「测什么」已锁定
      │
      ▼
④ ⚡ 基于测试点批量生成用例
   每个测试点节点 → 2~5 条详细用例
   「怎么测」在此阶段解决
      │
      ▼
⑤ 📋 用例审核 & 导出
   全链路溯源：用例 → 测试点 → 需求 → 迭代
```

**为什么要显式拆分这两步？**

| 决策 | 核心问题 | 评审方 | 错误代价 |
|---|---|---|---|
| 测试点（场景地图） | **测什么？** 覆盖哪些场景 | 测试工程师 + 产品经理可共同评审 | 低（改一行描述）|
| 用例生成 | **怎么测？** 具体步骤和数据 | 测试工程师 | 高（可能重写数十条用例）|

> 如果跳过测试点直接生成用例：发现覆盖方向错了，需要推倒重来一批用例。  
> 在测试点阶段对齐方向：一条测试点描述改一下，后续 5 条用例自动重新生成。

---

## ✨ 需求分析系统

### 6 类遗漏识别

| 遗漏类型 | AI 追问示例 |
|---|---|
| **异常路径缺失** | "§3.2 描述了同步成功流程，但未提及网络中断后的恢复策略" |
| **边界值未定义** | "`timeout` 为 Integer，未说明最大值、0值、负数的处理逻辑" |
| **权限场景缺失** | "数据源删除功能未说明：普通用户是否有删除权限？" |
| **并发竞争未说明** | "两个用户同时修改同一任务配置时，是否有锁机制？" |
| **状态流转不完整** | "任务状态有「执行中→成功/失败」，但未提及「暂停」和「取消」" |
| **跨模块关联缺口** | "§3.4 依赖 §2.2，但未说明数据源断开时调度任务的行为" |

### 多轮深挖 — 三层终止架构

```
第一轮：广度扫描 ── AI 列出所有疑似遗漏，用户快速标记优先级（~10分钟）
第二轮：深度聚焦 ── 逐条深挖「需讨论」项，每项最多 3 层追问
第三轮：交叉验证 ── 检查新增场景一致性，识别衍生缺口
终止条件：红色/灰色节点归零，或用户点击「完成」
```

### 内置行业必问清单（6大类 32 条，开箱即用）

<details>
<summary><b>🔁 幂等性类（6条）</b> — 触发：任何写入/更新操作</summary>

1. 重复执行此操作，结果是否一致？重复写入如何处理（覆盖/报错/忽略）？
2. 网络超时导致客户端重试时，服务端是否会产生重复数据？
3. 是否有唯一键/幂等键机制保障？
4. 批量操作中部分成功时，重试是全量还是仅重试失败部分？
5. 消息队列消费场景下，消息重复消费的处理策略？
6. 分布式事务失败后的补偿机制是否保证幂等？

</details>

<details>
<summary><b>⏰ 时区与时间类（5条）</b> — 触发：任何含时间戳的调度/记录</summary>

1. 时间字段是否涉及跨时区业务？存储格式是 UTC 还是本地时间？
2. Cron 表达式是基于哪个时区？DST（夏令时）切换时调度是否异常？
3. 跨天查询时，"今天"的边界是 00:00:00 还是业务自定义？
4. 历史数据回溯时，时区转换是否可能导致数据重复或丢失？
5. 时间范围查询的起止时间是否含端点（闭区间/开区间）？

</details>

<details>
<summary><b>📦 大数据量与性能类（5条）</b> — 触发：任何查询/导出/同步操作</summary>

1. 单次操作的数据量上限？超出如何处理（截断/报错/分批）？
2. 分页查询最大 pageSize？深分页（offset 极大）性能如何？
3. 导出功能最大数据量？超出是否支持异步导出+通知？
4. 索引字段是否覆盖所有筛选条件？大表全表扫描是否有超时保护？
5. 同步任务处理百万级数据时，内存管理策略是什么？

</details>

<details>
<summary><b>🔀 状态流转与并发类（6条）</b> — 触发：任何有状态机或共享资源的功能</summary>

1. 状态是否允许逆向流转（如：已完成 → 执行中）？
2. 多用户同时操作同一对象时，是乐观锁、悲观锁还是最后写入获胜？
3. 操作执行中对象被删除，正在执行的操作如何处理？
4. 并发创建同名对象时的冲突解决策略？
5. 任务执行中服务宕机重启，任务状态如何恢复？
6. 长时间运行的任务是否有超时强制终止机制？

</details>

<details>
<summary><b>💥 数据一致性与容错类（5条）</b> — 触发：任何跨系统/跨表操作</summary>

1. 操作失败时，已写入的部分数据如何处理（回滚/保留/标记）？
2. 跨数据源操作的原子性如何保证？是否支持分布式事务？
3. 数据源不可用时，是直接报错还是降级处理？
4. 数据同步中途中断，下次运行是全量重跑还是断点续传？
5. 源端和目标端 schema 不一致时（字段增减/类型变更），如何处理？

</details>

<details>
<summary><b>🔒 权限与安全类（5条）</b> — 触发：任何涉及数据访问或操作的功能</summary>

1. 普通用户是否可以访问/操作此功能？权限粒度到操作级还是数据级？
2. 越权访问（直接构造 URL/API）是否有服务端校验？
3. 敏感字段（手机号/身份证/密码）是否有脱敏展示？
4. 批量操作是否有数据量限制防止数据泄露？
5. API 接口是否有限流保护，防止暴力枚举？

</details>

---

## 🎯 测试点分析 & 场景地图确认

> **设计决策：测试点 = 场景地图节点，两者统一，不另起炉灶。**  
> 测试点分析是场景地图的前置确认步骤，是整个生成流程中最重要的「评审节点」。

### 为什么测试点必须前台可见

| 策略 | 问题 |
|---|---|
| ❌ 静默处理（底层自动生成测试点→直接生成用例） | 生成结果不对时，用户不知道是测试点方向错了还是用例步骤写错了，调试成本极高 |
| ✅ 前台显式确认 | 用户有一个清晰的「评审节点」：确认后再生成，方向错误在早期拦截 |

**额外价值**：测试点的粒度和语言对产品经理/业务方友好——他们看不懂用例的步骤格式，但能快速评审"这18个测试点覆盖了你的需求吗"，是最高效的评审层级。

### 测试点粒度规范

```
❌ 太粗（等于需求描述，没有指导意义）：
   - 验证数据同步功能正常

❌ 太细（等于用例步骤，跳过了抽象层）：
   - 验证输入 Host=192.168.1.100, Port=3306 时连接成功返回"连接成功"

✅ 合适粒度（一个测试点对应 2~5 条用例）：
   - 验证 MySQL/Oracle/PostgreSQL 数据源 JDBC 连接参数配置的有效性
   - 验证连接超时参数（timeout）的边界值处理行为
   - 验证连接失败时系统返回的错误提示可读性与准确性
   - 验证 SSL 证书配置场景下的连接安全性
   - 验证多用户并发配置同一数据源时的冲突处理
```

平台在 Prompt 中约束生成粒度，并在 UI 上展示每个测试点**预计生成 N 条用例**的预估，帮助用户判断是否需要拆分或合并。

### 测试点确认页面设计

```
┌─────────────────────────────────────────────────────────────────────┐
│  📋 REQ-089 · 测试点分析                      [导出] [全部采纳] [生成] │
│  ─────────────────────────────────────────────────────────────────  │
│  AI 已从需求文档 + 需求分析结果生成 18 个测试点草稿                    │
│  请确认覆盖范围，可增删改后点击「确认并生成用例」                        │
│                                                                     │
│  🟢 正常流程场景（4个）                                               │
│  ├─ [✏️] MySQL/Oracle/PostgreSQL 连接参数配置有效性    预计 3 条用例   │
│  ├─ [✏️] SSL 证书配置场景下的连接安全性                预计 2 条用例   │
│  ├─ [✏️] 连接池参数配置与连接数限制                    预计 3 条用例   │
│  └─ [✏️] 数据源分组管理与权限继承                      预计 2 条用例   │
│                                                                     │
│  🟡 边界值场景（5个）   [AI 识别补全]                                 │
│  ├─ [✏️] timeout 参数边界值处理（0/最大值/负数）       预计 4 条用例   │
│  ├─ [✏️] 连接池 maxSize=0 时的容错处理                预计 2 条用例   │
│  └─ ...                                                             │
│                                                                     │
│  🔴 异常场景（7个）     [AI 识别补全]                                 │
│  ├─ [✏️] 错误用户名/密码导致连接失败的错误提示          预计 3 条用例   │
│  ├─ [✏️] 数据库 Host 不可达时的超时与重试行为          预计 3 条用例   │
│  └─ ...                                                             │
│                                                                     │
│  ❓ 待确认（2个）       [需求分析追问后新增]                           │
│  ├─ [?] 并发修改同一数据源配置时的冲突处理（来自需求分析）              │
│  └─ [?] 数据源删除时正在执行的同步任务处理策略（来自需求分析）          │
│                                                                     │
│  [＋ 手动添加测试点]                                                  │
│                                                                     │
│  预计总用例数：52 条  │  覆盖：4个正常 + 5个边界 + 7个异常 + 2个待确认  │
│  [与PM分享评审链接]  [确认全部，开始生成用例 →]                        │
└─────────────────────────────────────────────────────────────────────┘
```

### 测试点与场景地图的统一关系

```
测试点（用户视角）         场景地图节点（系统内部）
────────────────────     ──────────────────────────────
测试点条目           ≡   scene_node（type, title, source, status）
绿色测试点           ≡   source: "document", status: "covered"
黄色测试点           ≡   source: "ai_detected", status: "supplemented"
红色待处理测试点      ≡   source: "ai_detected", status: "missing"
灰色待确认测试点      ≡   source: "ai_detected", status: "pending"
```

**同一份数据，两种展示方式**：
- 📋 **测试点列表视图**：按场景类型分组，显示预计用例数，适合评审确认
- 🌳 **场景地图可视化**（React Flow）：树形展示覆盖全貌，适合管理层汇报

### 用例与测试点的双向溯源

```
用例生成后，每条用例关联到来源测试点：

TC-089-003  ←→  测试点: "连接超时参数边界值处理"  ←→  REQ-089 §2.3
TC-089-004  ←→  测试点: "连接超时参数边界值处理"  ←→  REQ-089 §2.3
TC-089-005  ←→  测试点: "连接超时参数边界值处理"  ←→  REQ-089 §2.3

需求变更时：
  §2.3 变更 → 自动标记 "连接超时参数边界值处理" 测试点受影响
           → 自动标记 TC-089-003/004/005 需要复核
```

---

## ⚡ 对话式生成工作台

### 四种生成模式

| 模式 | 触发方式 | 特点 |
|---|---|---|
| 📄 文档驱动 | 选章节 → 一键生成 | 快速批量 |
| 💬 对话引导 | 自由对话描述 | 精细控制，灵活补充 |
| 🎯 **测试点驱动**（推荐） | 确认测试点 → 批量生成 | 质量最高，方向已确认 |
| 📋 模板填充 | 选模板 → 填变量 | 标准化，高效率 |

### 工作台三栏布局

```
┌──────────────────────────────────────────────────────────────────┐
│  左栏：需求导航              中栏：AI对话区         右栏：用例编辑   │
│  ───────────────────        ─────────────────────   ──────────   │
│  [子产品下拉]                [上下文指示器]          [统计栏]       │
│  [迭代选择]                  §2.2 + 企业规范 + 测试点              │
│                                                    [用例列表]     │
│  📁 Sprint3 需求             AI: 基于测试点「连接    TC-089-001   │
│   ├ REQ-089  已确认测试点     超时边界值」已生成      TC-089-002   │
│   ├ REQ-090  待诊断          3条用例...              ...          │
│   └ REQ-091  生成中                                              │
│                              [快捷指令栏]           [批量操作]     │
│  [测试点确认页]              异常/边界/并发/矩阵                    │
│  ⚡ 为选中需求生成            [输入框][发送]          [导出]        │
└──────────────────────────────────────────────────────────────────┘
```

---

## 📄 需求文档 Diff & 变更影响分析

### Diff 视图示例

```
REQ-089  v1.2 → v1.3
─────────────────────────────────────────────────────────────
  §2 功能描述
  - 编辑器每隔 30 秒触发一次自动保存          ← 🔴 删除
  + 编辑器每隔 10 秒触发一次自动保存          ← 🟢 新增
  + 用户可在设置中自定义间隔（5~60秒）        ← 🟢 新增

─────────────────────────────────────────────────────────────
影响分析
  🔴 测试点需重新生成    2 个  → 「超时边界值处理」「自定义间隔配置」
  🔴 用例需要重写        4 条  → TC-089-003、TC-089-007...
  🟡 用例需要复核       11 条  → TC-089-001、TC-089-012...
  🟢 不受影响          231 条

  [一键打开受影响测试点]  [重新生成受影响用例]  [导出 Diff 报告]
```

### Diff 引擎核心逻辑

```python
class DiffEngine:
    """两阶段 Diff：文本级（快速）+ 语义级（准确）"""

    def compute_diff(self, v_old: DocAST, v_new: DocAST) -> DiffResult:
        text_diff = self._myers_diff(v_old, v_new)
        # LLM 判断业务影响（防止"30秒改10秒"被误判为无关紧要措辞变化）
        semantic_impact = self._llm_impact_analysis(text_diff)
        return DiffResult(changed_nodes=text_diff.nodes,
                          impact_level=semantic_impact)

    async def find_affected(self, diff, project_id) -> AffectedReport:
        # 先找受影响的测试点，再找受影响的用例
        affected_nodes = await self._find_affected_scene_nodes(diff, project_id)
        affected_cases = await self._find_cases_by_nodes(affected_nodes)
        return AffectedReport(
            scene_nodes=affected_nodes,
            must_rewrite=self._filter(affected_cases, "high"),
            should_review=self._filter(affected_cases, "medium"),
        )
```

---

## 📊 需求覆盖度矩阵

```
子产品：离线开发 / 迭代：2025-Q2-Sprint3

                REQ-089  REQ-090  REQ-091  REQ-092  REQ-093  REQ-094
TC-OFFLINE-001    ✅       ·        ✅       ·        ·        ·
TC-OFFLINE-002    ·        ✅       ·        ✅       ·        ·
TC-OFFLINE-003    ·        ✅       ✅       ·        ·        ·
TC-OFFLINE-005    ·        ·        ·        ·        ·       ❌  ← 无测试点/用例覆盖

覆盖率：5/6  |  REQ-094「权限继承」尚未生成测试点  [一键生成测试点]
```

---

## 📈 执行结果回流 & 闭环飞轮（已推迟至 v2.0 GA）

| 执行结果 | 回流处理 | 对后续生成的影响 |
|---|---|---|
| 用例执行失败 | 记录失败原因 | AI 自动规避同类描述缺陷 |
| 用例被删除 | 标记删除原因 | 降低此类测试点的生成权重 |
| 高质量通过用例（评分≥4.5） | 进入优质用例库 | RAG 优先引用，作为 Few-shot |
| 用例人工修改记录 | 记录修改字段和内容 | 分析模式，优化 Prompt 模板 |
| **测试点被大幅修改** | **记录修改方向和原因** | **优化测试点生成策略** |

```
[需求录入] → [需求分析] → [测试点确认] → [用例生成] → [执行] → [结果回流]
      ↑_________________________________________________________________↓
              每轮迭代：生成质量↑  测试点准确率↑  人工修改量↓
```

---

## 📋 迭代测试计划自动生成（已裁剪）

```markdown
# 测试计划 — 离线开发 · 2025-Q2-Sprint3（自动草稿）

## 本迭代概况
- 需求：8 条  |  测试点：124 个  |  用例：312 条（新增 89 / 继承 223）
- 受变更影响需复核：12 条用例 / 3 个测试点

## 用例分布与执行建议
| 优先级 | 数量 | 建议执行时间 |
|--------|------|------------|
| P0 核心 | 23 条 | Day 1 上午（必须）|
| P1 重要 | 89 条 | Day 1 下午 + Day 2 |
| P2 一般 | 44 条 | Day 3（时间允许时）|

## 工作量预估
- 预计执行时间：3.2 人天（基于历史均速 12 分钟/条）

## 风险提示
- ⚠️ REQ-090 需求分析发现 3 处遗漏，测试点尚未完全确认
- ⚠️ REQ-089 从 v1.2 升至 v1.3，3 个测试点、12 条用例需复核
```

---

## 🛠 技术栈

### 前端

| 技术 | 版本 | 用途 |
|---|---|---|
| **Next.js** (App Router) | 16+ | 主框架 SSR/SSG |
| **bun** | latest | 包管理器 + 运行时（替代 npm/yarn） |
| **Biome** | 2+ | Lint + Format（替代 ESLint + Prettier） |
| **shadcn/ui** + Sonner | latest | UI 组件库 + Toast 通知 |
| **Zustand** + TanStack Query | latest | 全局状态 + 服务端状态缓存 |
| **TipTap** (ProseMirror) | 2+ | Requirement Card 编辑器 + 用例编辑 |
| **React Flow** | 11+ | 测试点场景地图可视化 |
| **Monaco Editor** | latest | JSON/Diff 代码视图，Prompt 编辑 |
| **Recharts / ECharts** | latest | 质量看板 + 覆盖度矩阵 |
| Tailwind CSS | 4+ | 原子化样式 |

### 后端

| 技术 | 版本 | 用途 |
|---|---|---|
| **Python** | 3.12+ | 运行时（统一版本，不再支持 3.11） |
| **uv** | latest | Python 环境与依赖管理（替代 pip/conda/poetry） |
| **ruff** | 0.8+ | Lint + Format（替代 flake8/black/isort） |
| **pyright** | 1.1+ | 静态类型检查（standard 模式） |
| **FastAPI** | 0.115+ | 主框架，异步 API + SSE 流式推送 |
| **SQLAlchemy 2.0** + Alembic | 2+ | ORM（async）+ 数据库迁移 |
| **Celery** + Redis | 5+ | 文档解析、Diff计算、诊断等异步任务 |
| python-docx + PyMuPDF | latest | Word/PDF 解析（UDA输入层） |
| PaddleOCR + GPT-4 Vision | — | 图片 OCR + 流程图/原型图理解 |
| **Myers Diff** + LangChain | — | 文本级 Diff + 语义影响分析 |
| httpx + BeautifulSoup | — | 外链图片/Confluence 内容抓取归档 |
| python-jose + passlib | — | JWT 认证 + RBAC 权限 |

### AI 引擎

| 技术 | 用途 |
|---|---|
| **LangChain** + **LangGraph** | Prompt 链编排，诊断/测试点/Diff Agent 工作流 |
| **智谱 GLM-4-Flash** / **阿里 Qwen-Max** | 主力模型（7提供商可配置：智谱/阿里/DeepSeek/月之暗面/OpenAI/Ollama/自定义） |
| **Ollama** (Qwen2.5-72B) | 私有化部署，数据不出内网 |
| **Qdrant** | 向量数据库，文档+知识库+历史测试点+用例 RAG |
| text-embedding-3-large / bge-m3 | 中英文双语 Embedding |
| **RAGAS** + 自定义评估 | 测试点质量评分 + 用例质量评分 + 回流权重计算 |

### 存储与基础设施

| 技术 | 用途 |
|---|---|
| **PostgreSQL 15+** | 核心业务数据（含 AST、Diff 历史、测试点） |
| **Redis 7+** | 缓存、分布式锁、任务队列 |
| **MinIO** / S3 | 原始文件归档 + 抓取图片存储 |
| Docker Compose / **K8s** + Helm | 容器化部署 |
| Prometheus + Grafana | 服务监控 + AI 调用量统计 |

---

## 🗄 数据模型

```sql
-- 子产品
CREATE TABLE products (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name       VARCHAR(100) NOT NULL,
    slug       VARCHAR(50) UNIQUE,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 迭代
CREATE TABLE iterations (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID NOT NULL REFERENCES products(id),
    name       VARCHAR(100) NOT NULL,
    start_date DATE,
    end_date   DATE,
    status     VARCHAR(20) DEFAULT 'active'
);

-- 需求卡片
CREATE TABLE requirements (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    iteration_id UUID NOT NULL REFERENCES iterations(id),
    req_id       VARCHAR(50) UNIQUE NOT NULL,
    title        TEXT NOT NULL,
    content_ast  JSONB NOT NULL,   -- UDA 内部 AST
    frontmatter  JSONB,
    status       VARCHAR(20) DEFAULT 'draft',
    version      INTEGER DEFAULT 1,
    created_at   TIMESTAMPTZ DEFAULT now()
);

-- 需求版本历史（用于 Diff）
CREATE TABLE requirement_versions (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    requirement_id UUID NOT NULL REFERENCES requirements(id),
    version        INTEGER NOT NULL,
    content_ast    JSONB NOT NULL,
    change_summary TEXT,
    created_at     TIMESTAMPTZ DEFAULT now(),
    UNIQUE(requirement_id, version)
);

-- Diff 记录
CREATE TABLE requirement_diffs (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    requirement_id UUID NOT NULL REFERENCES requirements(id),
    version_from   INTEGER NOT NULL,
    version_to     INTEGER NOT NULL,
    diff_nodes     JSONB,   -- 变更节点列表（含类型/影响评估）
    affected_cases JSONB,   -- {must_rewrite: [...], should_review: [...]}
    status         VARCHAR(20) DEFAULT 'pending',
    created_at     TIMESTAMPTZ DEFAULT now()
);

-- 归档图片
CREATE TABLE archived_images (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    original_url   TEXT NOT NULL,
    storage_path   TEXT NOT NULL,
    ocr_text       TEXT,
    vision_desc    TEXT,
    requirement_id UUID REFERENCES requirements(id),
    created_at     TIMESTAMPTZ DEFAULT now()
);

-- 需求健康报告
CREATE TABLE diagnosis_reports (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    requirement_id UUID NOT NULL REFERENCES requirements(id),
    risk_summary   JSONB,
    issues         JSONB,
    status         VARCHAR(20),
    created_at     TIMESTAMPTZ DEFAULT now()
);

-- 场景地图（测试点集合）
CREATE TABLE scene_maps (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    requirement_id UUID NOT NULL REFERENCES requirements(id),
    nodes          JSONB,   -- 节点树（含颜色/状态/来源/预计用例数）
    edges          JSONB,
    stats          JSONB,   -- {green, yellow, red, gray, total_estimated_cases}
    confirmed_at   TIMESTAMPTZ,   -- 用户确认时间，非空即代表测试点已锁定
    version        INTEGER DEFAULT 1,
    created_at     TIMESTAMPTZ DEFAULT now()
);

-- 场景节点（测试点）
CREATE TABLE scene_nodes (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    map_id          UUID NOT NULL REFERENCES scene_maps(id),
    parent_id       UUID REFERENCES scene_nodes(id),
    module_path     TEXT,
    scenario_type   VARCHAR(30),   -- normal|exception|boundary|concurrent|permission
    title           TEXT NOT NULL,
    source          VARCHAR(20),   -- document|ai_detected|user_added
    status          VARCHAR(20),   -- covered|supplemented|missing|pending|confirmed
    estimated_cases SMALLINT,      -- 预计生成用例数（粒度参考）
    created_at      TIMESTAMPTZ DEFAULT now()
);

-- 测试用例（全链路溯源：用例 → 测试点 → 需求 → 迭代）
CREATE TABLE test_cases (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id       UUID NOT NULL REFERENCES projects(id),
    requirement_id   UUID REFERENCES requirements(id),
    scene_node_id    UUID REFERENCES scene_nodes(id),   -- 来源测试点
    tc_id            VARCHAR(50) UNIQUE NOT NULL,
    title            TEXT NOT NULL,
    tc_type          VARCHAR(30),
    priority         VARCHAR(5),
    preconditions    TEXT,
    steps            JSONB,
    test_data        JSONB,
    ai_source        JSONB,
    execution_result JSONB,   -- 回流字段
    status           VARCHAR(20) DEFAULT 'draft',
    version          INTEGER DEFAULT 1,
    created_at       TIMESTAMPTZ DEFAULT now()
);

-- 操作审计日志（M20）
CREATE TABLE audit_logs (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID REFERENCES users(id),
    action      VARCHAR(50) NOT NULL,     -- create|update|delete|export|generate
    resource    VARCHAR(50) NOT NULL,     -- requirement|testcase|scene_node|...
    resource_id UUID,
    detail      JSONB,
    ip_address  TEXT,
    created_at  TIMESTAMPTZ DEFAULT now()
);

-- 通知（M16）
CREATE TABLE notifications (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id),
    type        VARCHAR(30) NOT NULL,
    title       TEXT NOT NULL,
    content     TEXT,
    ref_type    VARCHAR(50),
    ref_id      UUID,
    is_read     BOOLEAN DEFAULT false,
    created_at  TIMESTAMPTZ DEFAULT now(),
    updated_at  TIMESTAMPTZ DEFAULT now(),
    deleted_at  TIMESTAMPTZ DEFAULT NULL
);
```

> **软删除**：所有核心业务表均包含 `deleted_at TIMESTAMPTZ DEFAULT NULL` 字段，查询时过滤 `WHERE deleted_at IS NULL`，支持通过回收站（M21）恢复误删数据。

---

## 📡 API 设计

### 需求管理

```
POST   /api/products/:pid/iterations/:iid/requirements       创建需求卡片
PATCH  /api/requirements/:id                                  更新（自动版本快照）
GET    /api/requirements/:id/versions/:v1/diff/:v2            两版本 Diff
GET    /api/requirements/:id/diff/latest/affected             最新 Diff 影响分析
```

### UDA 解析与导出

```
POST   /api/parse                      解析任意格式 → AST（异步）
GET    /api/tasks/:task_id/status      查询任务进度
POST   /api/export                     AST → 任意格式
       body: { content_ast, format: "md|docx|pdf|xlsx|xmind|png" }
```

### 需求分析

```
POST   /api/requirements/:id/diagnose              触发需求分析
GET    /api/requirements/:id/diagnosis             获取分析报告
POST   /api/diagnosis/:report_id/sessions          创建场景补全会话
POST   /api/sessions/:sid/messages/stream          追问消息（SSE 流式）
```

### 测试点分析

```
POST   /api/requirements/:id/scene-map/generate    AI 生成测试点草稿（基于需求+诊断结果）
GET    /api/requirements/:id/scene-map             获取测试点场景地图
PATCH  /api/requirements/:id/scene-map/nodes       用户编辑测试点（增删改）
POST   /api/requirements/:id/scene-map/confirm     用户确认测试点（锁定，触发用例生成）
POST   /api/requirements/:id/scene-map/export      导出测试点（png/md/json）
```

### 用例生成

```
POST   /api/generate/from-scene-map/stream         测试点驱动生成（SSE，推荐）
POST   /api/generate/stream                        文档驱动 / 对话引导（SSE）
POST   /api/generate/from-template/stream          模板填充（SSE）
```

### 执行回流 & 分析

```
POST   /api/testcases/:id/execution-result         上报执行结果
PATCH  /api/testcases/batch/execution-result       批量上报（Jira/Xray 回写）
GET    /api/iterations/:id/test-plan               迭代测试计划（自动草稿）
GET    /api/iterations/:id/coverage-matrix         需求覆盖度矩阵
```

---

## 🗺 开发路线图

```
MVP v0.1 — 基础平台
├── ✅ 用户认证、子产品/迭代/需求三级结构
├── ✅ Requirement Card 编辑器
├── ✅ UDA 层基础版（Word/PDF/MD 解析）
└── ✅ 基础用例生成

Alpha v0.2 — 工作台
├── ✅ 历史数据导入 + 导入健康报告
├── ✅ 三栏工作台（流式生成 + 四种模式）
├── ✅ 用例 CRUD + 多格式导出
└── ✅ RAG 知识库集成

Beta v1.0 — 诊断 + 测试点
├── ✅ 需求分析系统（6类遗漏识别 + 苏格拉底追问）
├── ✅ 测试点分析 + 场景地图确认
├── ✅ 需求 Diff 引擎 + 影响分析
├── ✅ 覆盖度矩阵
└── ✅ 全量 API 实现（18个模块）

v2.0.0-rc — 全面重构 ← 当前版本
├── ✅ UI 重构：antd → shadcn/ui，统一 sy-* 设计 Token
├── ✅ 导航精简：13 → 9 菜单项（分析台 + 工作台合并）
├── ✅ AI 配置增强：7提供商多模型管理 + Prompt版本管理
├── ✅ 用例库增强：3级目录树 + 5步导入向导 + 多格式导出
├── ✅ 知识库 4 分类 + 模板库双Tab
├── ✅ 全局搜索 Cmd+K + 新手引导
├── ✅ 文案标准化：「诊断」→「分析」全站统一
├── ✅ RAG 阈值优化：0.3 → 0.72
├── ✅ 模块裁剪：M09/M18 裁剪，M13 推迟，M14 合并至仪表盘
└── 🎯 验收中：前后端构建验证 + 集成测试

v2.0.0 GA — 生产就绪
├── 🔲 端到端测试覆盖
├── 🔲 执行结果回流（M13）
├── 🔲 200 并发压测通过
└── 🔲 安全加固 + SSO 集成
```

---

## 🚀 快速开始

### 环境要求

- Docker & Docker Compose 2.0+  |  Python 3.12+  |  uv  |  bun
- OpenAI API Key（或私有化模型服务）

### 一键启动（推荐）

```bash
git clone https://github.com/koco-co/Sisyphus-case-platform.git && cd Sisyphus-case-platform
./init.sh   # 自动完成所有步骤：检查依赖 → 安装 → 启动 Docker → 迁移 → seed → 启动前后端
```

若前端依赖安装卡在 “Resolving”，脚本会在 120 秒后自动改用国内镜像重试；也可直接指定镜像：`BUN_REGISTRY=https://registry.npmmirror.com ./init.sh`。

### 手动分步启动

```bash
git clone https://github.com/koco-co/Sisyphus-case-platform.git && cd Sisyphus-case-platform
cp .env.example .env   # 编辑 .env 填入 OPENAI_API_KEY

docker compose -f docker/docker-compose.yml up -d   # 启动基础设施

cd backend && uv sync --all-extras                  # 安装后端依赖
uv run alembic upgrade head                          # 数据库迁移
uv run python scripts/seed.py                        # 初始化种子数据

uv run uvicorn app.main:app --reload --port 8000 &  # 启动 API 服务
uv run celery -A app.worker.celery_app worker --loglevel=info &  # 启动异步任务

cd ../frontend && bun install && bun dev   # → http://localhost:3000
```

### 私有化部署（数据不出内网）

```bash
docker run -d --gpus all -v ollama_data:/root/.ollama \
  -p 11434:11434 ollama/ollama
ollama pull qwen2.5:72b && ollama pull bge-m3

# .env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
DISABLE_EXTERNAL_API=true
IMAGE_ARCHIVE_EXTERNAL=false
```

### 生产 K8s 部署

```bash
helm repo add Sisyphus-case-platform https://charts.Sisyphus-case-platform.io
helm install Sisyphus-case-platform Sisyphus-case-platform/Sisyphus-case-platform \
  --set global.openaiApiKey="sk-..." \
  -f values-production.yaml
```

---

## 🤝 贡献指南

- 📋 **行业必问清单扩展** — 电商/金融/医疗等行业的必问问题
- 🏭 **测试模板贡献** — 适合特定系统类型的模板
- 🔌 **集成插件** — Azure DevOps、Zephyr、TestRail 等
- 🧹 **清洗规则适配** — 禅道/TAPD 等工具的历史用例 CSV 格式
- 🎯 **测试点粒度规范** — 针对特定业务领域的粒度校准规则

---

## 📄 License

Enterprise License — 商业使用请联系授权

---

<div align="center">
**Sisyphus-case-platform** · AI 驱动的企业级测试用例生成平台

*测什么（测试点）先于怎么测（用例），方向对了才是真的快*

*生成 → 执行 → 回流 → 更好的生成 · 持续进化的质量飞轮*

</div>
