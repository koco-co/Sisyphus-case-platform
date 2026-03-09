# Sisyphus-Y 开发任务清单 v1.0

> **项目名称**：Sisyphus-Y
> **原型参考**：`Sisyphus-Y.html`（唯一视觉标准，所有 UI 细节以此为准，不得自行发挥）
> **仓库地址**：https://github.com/koco-co/Sisyphus-case-platform.git
> **当前最严重 Bug**（见截图）：生成工作台中间区域直接渲染原始 JSON 字符串，必须第一优先修复

---

## 一、技术栈总览

| 层级               | 技术                              | 版本       | 说明                                                                |
| ------------------ | --------------------------------- | ---------- | ------------------------------------------------------------------- |
| 前端框架           | React + TypeScript                | 18 / 5     | —                                                                   |
| 样式方案           | Tailwind CSS                      | v3         | 所有颜色/间距必须用 Tailwind class，禁止内联 style 硬编码色值       |
| 组件库             | shadcn/ui                         | latest     | Button / Input / Badge / Table / Select / Switch / Tabs / Dialog 等 |
| 图标库             | lucide-react                      | latest     | **所有图标来自此库，禁止使用 emoji 作为 UI 元素**                   |
| 状态管理           | Zustand                           | latest     | —                                                                   |
| 路由               | React Router                      | v6         | —                                                                   |
| 流式输出           | fetch + ReadableStream            | —          | SSE 流式接收后端生成内容                                            |
| 可视化（场景地图） | React Flow                        | v11+       | 测试点确认页场景地图                                                |
| 图表（看板）       | Recharts                          | latest     | 质量看板图表                                                        |
| **后端框架**       | **FastAPI**                       | **0.110+** | Python 3.11+                                                        |
| **AI 调用**        | **LangChain + LiteLLM**           | latest     | 支持 GPT-4o / Claude / Ollama 切换                                  |
| **文档解析**       | **python-docx / pypdf / PyMuPDF** | latest     | Word / PDF 解析                                                     |
| **OCR**            | **PaddleOCR**                     | latest     | 扫描件 PDF / 图片文字提取                                           |
| **向量数据库**     | **Qdrant**                        | latest     | RAG 知识库检索                                                      |
| **任务队列**       | **Celery + Redis**                | latest     | 异步解析、异步向量化                                                |
| **关系数据库**     | **PostgreSQL**                    | 15+        | 主业务数据                                                          |
| **对象存储**       | **MinIO**                         | latest     | 图片/文档归档                                                       |
| **文本 Diff**      | **difflib（Myers 算法）**         | stdlib     | 需求变更分析                                                        |

---

## 二、Tailwind 主题配置（必须完整配置，禁止任何硬编码色值）

在 `tailwind.config.ts` 中扩展以下内容，整个项目通过 class 引用颜色，绝不在组件里写 `#00d9a3`：

```ts
// tailwind.config.ts
import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // 背景层级（从深到浅）
        "sy-bg": "#0d0f12", // 最底层页面背景
        "sy-bg-1": "#131619", // 侧边栏、顶栏、卡片
        "sy-bg-2": "#1a1e24", // 输入框、hover 背景、二级卡片
        "sy-bg-3": "#212730", // 标签、徽章、三级容器
        // 边框
        "sy-border": "#2a313d",
        "sy-border-2": "#353d4a",
        // 文字
        "sy-text": "#e2e8f0", // 主要文字
        "sy-text-2": "#94a3b8", // 次要文字
        "sy-text-3": "#566577", // 辅助文字、占位符
        // 品牌色
        "sy-accent": "#00d9a3",
        "sy-accent-2": "#00b386",
        // 语义色
        "sy-warn": "#f59e0b",
        "sy-danger": "#f43f5e",
        "sy-info": "#3b82f6",
        "sy-purple": "#a855f7",
      },
      fontFamily: {
        sans: ["DM Sans", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
        display: ["Syne", "sans-serif"],
      },
      keyframes: {
        blink: { "0%,100%": { opacity: "1" }, "50%": { opacity: "0" } },
        "fade-in": {
          from: { opacity: "0", transform: "translateY(2px)" },
          to: { opacity: "1", transform: "none" },
        },
      },
      animation: {
        blink: "blink 0.8s infinite",
        "fade-in": "fade-in 0.15s ease-out",
      },
    },
  },
  plugins: [],
};
export default config;
```

**Google Fonts 引入**（`index.html` head 中）：

```html
<link
  href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500;600&family=Syne:wght@600;700;800&display=swap"
  rel="stylesheet"
/>
```

---

## 三、图标对照表（emoji → lucide-react，全项目统一）

| 语义 / 位置     | lucide-react 组件                      |
| --------------- | -------------------------------------- |
| 项目列表导航    | `<LayoutGrid />`                       |
| 需求文档        | `<FileText />`                         |
| 健康诊断        | `<Stethoscope />`                      |
| 测试点确认      | `<Target />`                           |
| 生成工作台      | `<Zap />`                              |
| 用例管理        | `<ClipboardList />`                    |
| Diff 视图       | `<GitCompare />`                       |
| 覆盖矩阵        | `<Grid3X3 />`                          |
| 质量看板        | `<BarChart2 />`                        |
| 知识库          | `<BookOpen />`                         |
| 模板库          | `<Layers />`                           |
| 系统设置        | `<Settings />`                         |
| 新建 / 添加     | `<Plus />`                             |
| 搜索            | `<Search />`                           |
| 编辑            | `<Pencil />`                           |
| 删除            | `<Trash2 />`                           |
| 导出 / 下载     | `<Download />`                         |
| 警告 / 告警     | `<AlertTriangle />`                    |
| 已完成 / 已确认 | `<CheckCircle2 />`                     |
| 生成中（转圈）  | `<Loader2 className="animate-spin" />` |
| 发送消息        | `<Send />`                             |
| 用户头像        | `<User />`                             |
| AI 标识         | `<Bot />`                              |
| 筛选            | `<SlidersHorizontal />`                |
| 场景地图        | `<Network />`                          |
| 知识库 RAG      | `<Database />`                         |
| AI 补全 / 魔法  | `<Sparkles />`                         |
| 暂停生成        | `<Square />`                           |
| 分析 / 脑图     | `<Brain />`                            |
| 流程步骤箭头    | `<ChevronRight />`                     |
| 折叠 / 展开     | `<ChevronDown />` / `<ChevronUp />`    |
| 版本历史        | `<History />`                          |
| 链接 / 分享     | `<Link2 />`                            |
| 钟 / 最近       | `<Clock />`                            |
| 星级 / 质量     | `<Star />`                             |
| 锁定            | `<Lock />`                             |
| 成员 / 团队     | `<Users />`                            |

---

## 四、全局复用组件规范

### 4.1 StatusBadge（状态药丸）

封装 shadcn/ui `Badge`，全项目统一调用，禁止各页面自己实现：

```tsx
// src/components/ui/StatusBadge.tsx
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

type Variant = "success" | "warning" | "danger" | "info" | "purple" | "gray";

const variantStyles: Record<Variant, string> = {
  success: "bg-sy-accent/10 text-sy-accent border border-sy-accent/25",
  warning: "bg-sy-warn/10 text-sy-warn border border-sy-warn/25",
  danger: "bg-sy-danger/10 text-sy-danger border border-sy-danger/25",
  info: "bg-sy-info/10 text-sy-info border border-sy-info/25",
  purple: "bg-sy-purple/10 text-sy-purple border border-sy-purple/25",
  gray: "bg-sy-bg-3 text-sy-text-3 border border-sy-border",
};

export function StatusBadge({
  variant = "gray",
  children,
  className,
}: {
  variant?: Variant;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 px-2 py-0.5 rounded-full",
        "font-mono text-[11px] font-medium",
        variantStyles[variant],
        className,
      )}
    >
      {children}
    </span>
  );
}
```

**用法**：

```tsx
<StatusBadge variant="danger">P0</StatusBadge>
<StatusBadge variant="success"><CheckCircle2 size={10} /> 已生成</StatusBadge>
<StatusBadge variant="warning"><Loader2 size={10} className="animate-spin" /> 生成中</StatusBadge>
```

### 4.2 三栏固定高度布局（ThreeColLayout）

用于：生成工作台 / 健康诊断 / 测试点确认：

```tsx
// src/components/layout/ThreeColLayout.tsx
export function ThreeColLayout({
  left,
  center,
  right,
  leftWidth = "240px",
  rightWidth = "340px",
}: {
  left: React.ReactNode;
  center: React.ReactNode;
  right: React.ReactNode;
  leftWidth?: string;
  rightWidth?: string;
}) {
  return (
    <div
      className="flex border border-sy-border rounded-xl overflow-hidden bg-sy-bg-1"
      style={{ height: "calc(100vh - 49px - 48px)" }} // 顶栏 + 子导航高度
    >
      {/* 左栏：固定宽度，独立滚动 */}
      <div
        className="shrink-0 border-r border-sy-border overflow-y-auto"
        style={{ width: leftWidth }}
      >
        {left}
      </div>

      {/* 中栏：弹性宽度，独立滚动 */}
      <div className="flex-1 overflow-y-auto min-w-0">{center}</div>

      {/* 右栏：固定宽度，独立滚动 */}
      <div
        className="shrink-0 border-l border-sy-border overflow-y-auto"
        style={{ width: rightWidth }}
      >
        {right}
      </div>
    </div>
  );
}
```

### 4.3 StreamCursor（流式生成光标）

```tsx
// src/components/workspace/StreamCursor.tsx
export function StreamCursor() {
  return (
    <span className="inline-block w-0.5 h-3.5 bg-sy-warn rounded-sm align-middle ml-1 animate-blink" />
  );
}
```

---

## 五、前端页面任务（F-TASK）

---

### ★ F-TASK-01 · 生成工作台 — 最高优先级修复（P0）

**核心问题**：当前版本在中间区域直接渲染原始 JSON 对象字符串。必须替换为格式化用例卡片组件。

#### 5.1.1 CaseCard 组件（核心，禁止 JSON.stringify 展示）

```tsx
// src/components/workspace/CaseCard.tsx
import { CheckCircle2, Loader2, Pencil } from "lucide-react";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { StreamCursor } from "./StreamCursor";

export interface TestCaseStep {
  step_num: number;
  action: string;
  expected_result?: string;
}

export interface TestCase {
  id: string;
  title: string;
  priority: "P0" | "P1" | "P2";
  case_type: "normal" | "exception" | "boundary" | "concurrent" | "permission";
  precondition?: string;
  steps: TestCaseStep[];
  source_node_id?: string;
  source_node_title?: string;
  status: "generating" | "done" | "needs_rewrite" | "needs_review";
  ai_generated: boolean;
}

const PRIORITY_VARIANT = { P0: "danger", P1: "warning", P2: "info" } as const;
const CASE_TYPE_LABEL = {
  normal: "正常流程",
  exception: "异常场景",
  boundary: "边界值",
  concurrent: "并发",
  permission: "权限",
};

export function CaseCard({ testCase }: { testCase: TestCase }) {
  return (
    <div
      className={[
        "rounded-lg p-3 mb-2 border transition-colors animate-fade-in",
        testCase.status === "generating"
          ? "bg-sy-bg-2 border-sy-warn/25"
          : "bg-sy-bg-2 border-sy-border hover:border-sy-border-2",
      ].join(" ")}
    >
      {/* ── 标题行 ── */}
      <div className="flex items-center gap-2 mb-1.5 flex-wrap">
        <span className="font-mono text-[11px] text-sy-text-3 shrink-0">
          {testCase.id}
        </span>
        <StatusBadge variant={PRIORITY_VARIANT[testCase.priority]}>
          {testCase.priority}
        </StatusBadge>
        <StatusBadge variant="gray">
          {CASE_TYPE_LABEL[testCase.case_type]}
        </StatusBadge>

        {testCase.status === "done" && (
          <StatusBadge variant="success">
            <CheckCircle2 size={10} />
            已生成
          </StatusBadge>
        )}
        {testCase.status === "generating" && (
          <StatusBadge variant="warning">
            <Loader2 size={10} className="animate-spin" />
            生成中
          </StatusBadge>
        )}
        {testCase.status === "needs_rewrite" && (
          <StatusBadge variant="danger">需重写</StatusBadge>
        )}

        <button className="ml-auto p-1 rounded hover:bg-sy-bg-3 text-sy-text-3 hover:text-sy-text transition-colors">
          <Pencil size={12} />
        </button>
      </div>

      {/* ── 用例标题 ── */}
      <p className="text-[12.5px] font-medium text-sy-text mb-1.5 leading-snug">
        {testCase.title}
        {testCase.status === "generating" && <StreamCursor />}
      </p>

      {/* ── 前置条件 ── */}
      {testCase.precondition && (
        <p className="text-[11.5px] text-sy-text-3 mb-2 leading-relaxed">
          前置：{testCase.precondition}
        </p>
      )}

      {/* ── 步骤列表（核心修复：逐条渲染，永远不用 JSON.stringify）── */}
      <div className="space-y-0">
        {testCase.steps?.map((step) => (
          <div
            key={step.step_num}
            className="flex gap-2 pt-1 mt-1 border-t border-sy-border text-[11.5px] text-sy-text-2"
          >
            <span className="font-mono text-[11px] text-sy-accent font-semibold w-4 shrink-0 pt-px">
              {step.step_num}
            </span>
            <span className="leading-relaxed">{step.action}</span>
          </div>
        ))}
      </div>

      {/* ── 预期结果（用 accent 色区分）── */}
      {testCase.steps?.at(-1)?.expected_result && (
        <div className="flex gap-2 pt-1 mt-1 border-t border-sy-border text-[11.5px] text-sy-accent">
          <CheckCircle2 size={12} className="shrink-0 mt-0.5" />
          <span className="leading-relaxed">
            {testCase.steps.at(-1)!.expected_result}
          </span>
        </div>
      )}

      {/* ── 来源溯源 ── */}
      {testCase.source_node_title && (
        <p className="text-[11px] text-sy-text-3 mt-2">
          来源：测试点「{testCase.source_node_title}」
        </p>
      )}
    </div>
  );
}
```

#### 5.1.2 工作台整体布局规范

**子导航栏**（shadcn/ui Tabs 组件，高度 40px）：

```
背景 bg-sy-bg-1，下边框 border-b border-sy-border
四个标签：测试点驱动 | 探索式 | 模板驱动 | 批量生成
激活态：bg-sy-accent text-black font-semibold rounded-md
右侧：批量导出 Button（variant="outline" size="sm"，<Download size={14} /> 图标）
```

使用 `ThreeColLayout leftWidth="240px" rightWidth="340px"`。

**左栏（240px）——需求导航**：

- 顶部 shadcn/ui Select：选择子产品/迭代
- 统计文字：`font-mono text-[10.5px] text-sy-text-3`，格式 `8条需求 · 124个测试点`
- 需求列表（shadcn/ui ScrollArea）：
  - 激活项：`bg-sy-accent/10 border border-sy-accent/25 rounded-md`
  - 状态圆点：`w-1.5 h-1.5 rounded-full`，颜色 sy-accent/sy-danger/sy-text-3
  - 需求 ID：`font-mono text-[12px] font-semibold text-sy-text`
  - 右侧 StatusBadge
  - 需求标题：`text-[11.5px] text-sy-text-2 ml-3.5`
  - 子测试点展开：激活需求下方缩进，`text-[11px]`，激活用 `text-sy-accent`
- 底部上下文注入区：`bg-sy-bg-2 border border-sy-border rounded-md p-2`，已注入标签用 StatusBadge

**中栏（flex:1）——AI 对话与用例渲染**：

- 列头：sticky，右侧模型标识（StatusBadge info + 温度数字 font-mono）
- 系统横幅（居中）：`font-mono text-[10.5px] bg-sy-bg-2 border border-sy-border rounded-full px-3 py-0.5`
- 消息列表（shadcn/ui ScrollArea）：
  - AI 消息气泡：`bg-sy-accent/4 border border-sy-accent/20 rounded-lg p-2.5 max-w-[440px]`
  - 用户消息气泡：`bg-sy-bg-2 border border-sy-border rounded-lg p-2.5`（右对齐）
  - AI 头像：28px 圆形，`bg-gradient-to-br from-sy-accent/20 to-sy-info/15 border border-sy-accent/30`，`<Bot size={14} className="text-sy-accent" />`
  - **✅ 用例数据必须渲染为 `<CaseCard>` 组件，绝对禁止 JSON.stringify**
- 快捷指令栏：`bg-sy-bg-1 border border-sy-border rounded-lg p-2`，多个 Button size="sm" variant="outline"
- 底部输入区：shadcn/ui Textarea（resize-none h-[52px]）+ `<Send size={16} />` 发送按钮（btn-primary）+ `<Square size={14} />` 暂停按钮

**右栏（340px）——已生成用例**：

- 列头：`<ClipboardList size={14} />` 已生成用例 + 计数（`font-mono text-[10px] text-sy-accent`）+ `<Download size={13} />` 导出
- 统计行：已生成 N（accent）/ 生成中 N（warn）/ 待生成 N（text-3）
- 筛选（shadcn/ui ToggleGroup）：全部 / P0 / P1 / 异常 / 边界
- 用例列表（ScrollArea）：每条 `bg-sy-bg-2 border border-sy-border rounded-md p-2 mb-1 cursor-pointer`，激活态 `bg-sy-accent/10 border-sy-accent/25`
- 待生成骨架：shadcn/ui Skeleton，`border-dashed border-sy-border rounded-md`
- 底部批量操作：3 个全宽 Button variant="outline" size="sm"（Excel / XMind / Jira）

---

### F-TASK-02 · 项目列表（P0）

布局：无侧边栏，`max-w-[1200px] mx-auto px-6 py-6`

**4 格统计卡片**（shadcn/ui Card）：

- 卡片 1（accent 主题）：`border-sy-accent/25 bg-sy-accent/4`，数字 `font-mono text-[26px] font-semibold text-sy-accent`
- 覆盖率卡片：数字下方加 shadcn/ui Progress `className="h-[3px] mt-1.5"`
- 趋势文字：`font-mono text-[11px]`，上升 text-sy-accent，下降 text-sy-danger

**子产品筛选**：shadcn/ui ToggleGroup（多选）

**项目卡片网格**（grid-cols-3 gap-4）：

- shadcn/ui Card，`hover:-translate-y-px hover:border-sy-border-2 transition-all cursor-pointer`
- 图标容器：`w-9 h-9 rounded-lg`，渐变背景 + 对应色系 1px 边框
- 数据格：`grid grid-cols-3 gap-2 my-3`，每格 `bg-sy-bg-2 rounded-md text-center p-2`
- 进度条：shadcn/ui Progress `className="h-[4px] mb-3"`
- 底部：`<Users size={13} />` + 成员名单（text-[11.5px]）+ 右侧 StatusBadge

**最近动态**：shadcn/ui Table（bg-sy-bg-1 border border-sy-border rounded-xl overflow-hidden）

---

### F-TASK-03 · 需求卡片编辑器（P0）

**左侧边栏（220px）**：

- 层级：子产品 → 迭代 → 需求列表
- 需求项：状态圆点 + ID（font-mono）+ StatusBadge + 标题
- 新建：`<Plus size={13} />` Button variant="outline"，`border-dashed border-sy-accent/40 text-sy-accent w-full`

**主内容区**：

- 元数据栏：`bg-sy-bg-1 border border-sy-border rounded-lg px-3.5 py-2.5 mb-5 flex gap-5 flex-wrap items-center`
  - 优先级/负责人/标签均用 StatusBadge 或 shadcn/ui Badge
  - 诊断警告：StatusBadge warning + `<AlertTriangle size={12} />` + "开始诊断" Button size="sm"
- 工具栏：Bold / Italic 等用 `<Bold size={14} />` / `<Italic size={14} />` 等 lucide 图标，shadcn/ui Separator 分组，`<Sparkles size={14} className="text-sy-accent" />` AI 补全
- 正文区 `px-8 py-6 max-w-[760px] leading-relaxed`：
  - Frontmatter 块：`font-mono text-[11px] bg-sy-bg-2 border border-sy-border rounded-md p-3`，字段名 `text-sy-accent`
  - 章节标题：`font-display text-lg font-bold border-b-2 border-sy-border pb-2 mb-4`
  - 待补充：`<Circle size={13} className="text-sy-text-3" />` + "填写" Button variant="ghost" size="sm"
  - 已确认：`<CheckCircle2 size={13} className="text-sy-accent" />`
  - 图片卡片：`bg-sy-bg-2 border border-sy-border rounded-lg p-3`，占位 `<ImageIcon size={24} className="opacity-40" />`，归档状态 `text-[10.5px] text-sy-accent`
- 底部关联面板（grid-cols-2 gap-4）：测试点卡片 + 用例卡片

---

### F-TASK-04 · 需求健康诊断（P0）

**左侧边栏**：流程步骤菜单：

- 已完成：`<CheckCircle2 size={14} className="text-sy-accent" />`，`text-sy-accent`
- 当前激活：`bg-sy-accent/10 border border-sy-accent/20 rounded-md text-sy-accent`
- 未开始：`opacity-40 text-sy-text-3`（cursor-not-allowed）

使用 `ThreeColLayout leftWidth="300px" rightWidth="280px"`。

**左栏（健康报告）**：

- 分组标题：`font-mono text-[11px] text-sy-text-3 uppercase tracking-widest my-2`
- 高风险条目：`bg-sy-bg-2 border border-sy-border border-l-[3px] border-l-sy-danger rounded-lg p-3 mb-1.5 cursor-pointer`，`<AlertTriangle size={13} className="text-sy-danger" />`
- 中风险：`border-l-sy-warn`，`<AlertTriangle size={13} className="text-sy-warn" />`
- 已处理：`border-l-sy-accent opacity-60`，`<CheckCircle2 size={13} className="text-sy-accent" />`

**中栏（场景补全对话）**：同 F-TASK-01 中栏消息气泡规范，底部三个按钮：发送 / 跳过 / 已知晓。

**右栏（场景地图预览）**：

- 4 格统计：`grid grid-cols-4 gap-1 mb-3`，各色浅背景小卡片，数字 `font-mono text-base font-semibold`
- 节点列表：`flex items-center gap-2 p-2 rounded-md border border-sy-border bg-sy-bg-2 mb-1 cursor-pointer`
  - 状态圆点：`w-2 h-2 rounded-full`，颜色对应 accent/warn/danger/text-3
  - 正在讨论中（红色节点）：`border-sy-danger/30 bg-sy-danger/4`
- 底部预估卡片：`bg-sy-bg-2 rounded-md border border-sy-border p-2`

---

### F-TASK-05 · 测试点确认（P0）

**顶部流程进度**：

```
padding 10px 20px，bg-sy-bg-1，border-b border-sy-border，flex items-center gap-2
步骤：<CheckCircle2 size={14} className="text-sy-accent" /> 文字（已完成）
    → <ChevronRight size={14} className="text-sy-border-2" />
    → bg-sy-bg-2 rounded-md px-3 py-1.5 font-medium text-sy-text（当前）
    → text-sy-text-3（未开始）
右侧：StatusBadge warning（告警数）+ 分享按钮 + 确认全部主按钮（btn-primary）
```

使用 `ThreeColLayout leftWidth="260px" rightWidth="300px"`。

**左栏（测试点列表）**：

- 4 格统计 + 分段进度条（`h-1.5 flex rounded-sm overflow-hidden my-2`，各色 `flex-[N]`）
- 分组标题：`font-mono text-[11px] text-sy-text-3 uppercase tracking-wider px-3 py-2`
- 测试点条目：
  - 正常（已覆盖）：shadcn/ui Checkbox checked，`text-sy-text`
  - 待处理红色：`border-l-2 border-l-sy-danger`，Checkbox 未选中 `data-[state=unchecked]:border-sy-danger`，标题 `text-sy-danger font-medium`
  - 待确认灰色：`text-sy-text-3`，Checkbox 未选中 `bg-sy-bg-3`
  - 右侧预计数：`font-mono text-[10px] text-sy-text-3 ml-auto`
- 底部新增：`<Plus size={13} />` Button variant="outline" `w-full border-dashed text-sy-accent border-sy-accent/40`

**中栏（测试点详情）**：

- 粒度提示横幅：`bg-sy-accent/6 border border-sy-accent/20 rounded-md p-2 flex gap-2 items-start mb-4`，`<Sparkles size={14} className="text-sy-accent shrink-0 mt-0.5" />`
- 预期用例列表：shadcn/ui Card，每条含优先级 Badge + 标题
- 来源：`bg-sy-bg-1 border border-sy-border rounded-lg p-3 text-[12px] text-sy-text-3 flex gap-2 flex-wrap`，`<Link2 size={12} />` 图标
- 待处理告警（红色节点时显示）：`bg-sy-danger/6 border border-sy-danger/30 rounded-lg p-3 mb-3`，`<AlertTriangle size={16} className="text-sy-danger" />`，三个操作按钮

**右栏（场景地图可视化）**：

- shadcn/ui ToggleGroup 切换图形/列表视图
- React Flow 容器：`bg-sy-bg rounded-lg border border-sy-border min-h-[420px] relative overflow-hidden`
- 节点样式：
  - 已覆盖：`bg-sy-accent/10 border border-sy-accent/35 text-sy-accent rounded-md px-3 py-1.5 text-[12px]`
  - AI 补全：`bg-sy-warn/10 border border-sy-warn/35 text-sy-warn`
  - 缺失（红）：`bg-sy-danger/10 border-[1.5px] border-sy-danger text-sy-danger font-semibold`
  - 待确认：`bg-sy-bg-3 border border-dashed border-sy-border-2 text-sy-text-3`
- 导出按钮组（3个）：`<Download size={13} />` PNG / `<FileText size={13} />` MD / `<Code size={13} />` JSON

---

### F-TASK-06 · 用例管理（P1）

**变更提醒横幅**（shadcn/ui Alert）：

```tsx
<Alert className="border-sy-danger/30 bg-sy-danger/6 mb-4">
  <Bell size={16} className="text-sy-danger" />
  <AlertTitle className="text-sy-text">需求变更影响 15 条用例</AlertTitle>
  <AlertDescription className="text-sy-text-3">
    REQ-089 v1.2→v1.3：4 条需要重写，11 条需要复核
  </AlertDescription>
  {/* 右侧：查看Diff + 一键重新生成 */}
</Alert>
```

**筛选工具栏**：多组 shadcn/ui ToggleGroup，竖向 Separator 分隔。

**表格**（shadcn/ui Table）：

- needs_rewrite 行：`bg-sy-danger/4`
- needs_review 行：`bg-sy-warn/3`
- 标题列内联 StatusBadge danger/warning（inline，size xs）
- 操作列：`<Pencil size={13} />` / `<Eye size={13} />` / `<ChevronRight size={13} />`

---

### F-TASK-07 · Diff 视图（P1）

布局：无侧边栏，`max-w-[1200px] mx-auto`，`grid grid-cols-2 gap-4`

**Diff 代码块**（Card padding-0）：

- 文件头：`bg-sy-bg-2 border-b border-sy-border px-3 py-2 font-mono text-[11.5px] flex items-center gap-2`
- 删除行：`bg-sy-danger/10 border-l-[3px] border-l-sy-danger px-3 py-1 font-mono text-[12px] text-sy-danger`
- 新增行：`bg-sy-accent/8 border-l-[3px] border-l-sy-accent px-3 py-1 font-mono text-[12px] text-sy-accent`
- 上下文行：`px-3 py-1 font-mono text-[12px] text-sy-text-3`

**AI 语义评估卡片**：`border-sy-warn/25 bg-sy-warn/3`，`<Brain size={16} className="text-sy-warn" />`

**右侧受影响用例**：

- 3 格统计（danger/warn/default 主题）
- 用例 Table（需重写行 bg-sy-danger/4）
- 新增测试点建议：`border-sy-accent/20 bg-sy-accent/3`，`<Sparkles size={14} className="text-sy-accent" />`

---

### F-TASK-08 · 质量看板（P1）

- 4 格统计卡片 + shadcn/ui Progress
- Recharts BarChart（覆盖率趋势，深色主题，fill `#00d9a3`，透明度渐进）
- Recharts PieChart（场景分布，innerRadius，各色 Cell）
- 覆盖矩阵：自定义 Table，未覆盖列 `bg-sy-danger/4`，`<X size={14} className="text-sy-danger" />`
- 执行回流时间线：Card 列表，`<Star size={13} />` / `<Pencil size={13} />` 等图标

---

### F-TASK-09 · 知识库（P1）

- RAG 横幅：`bg-sy-accent/6 border border-sy-accent/25 rounded-lg`，`<Database size={16} className="text-sy-accent" />`
- 文档 Table：向量化状态 StatusBadge（success "✓ 完成" / warning "⚡ 向量化中"），命中次数 `font-mono text-sy-accent`
- RAG 测试面板（grid-cols-2）：左侧 Textarea + `<Search size={15} />` 按钮，右侧结果列表，相似度 `font-mono`

---

### F-TASK-10 · 模板库（P1）

- 模板卡片（grid-cols-3）：shadcn/ui Card，`hover:-translate-y-0.5 cursor-pointer`
- 图标容器：`w-[38px] h-[38px] rounded-lg`，渐变背景
- 官方徽章：StatusBadge success
- 变量表单：`font-mono text-[11.5px] text-sy-accent w-[120px]` + shadcn/ui Input
- 新建占位卡：`border-dashed hover:border-sy-accent/40 hover:text-sy-accent`，`<Plus size={28} className="opacity-40" />`

---

### F-TASK-11 · 系统设置（P1）

- AI 模型卡片（grid-cols-3）：激活态 `bg-sy-accent/10 border-[1.5px] border-sy-accent/40`，右上角 `w-2 h-2 rounded-full bg-sy-accent`
- 功能开关：每行 `flex items-center justify-between py-3 border-b border-sy-border`，右侧 shadcn/ui Switch
- 外部集成（Jira/飞书）：连接态 StatusBadge success，未连接 Button variant="outline"

---

## 六、后端 Python 任务（B-TASK）

---

### B-TASK-01 · 工程初始化（P0）

**目录结构**：

```
backend/
├── main.py                        # FastAPI 应用入口
├── requirements.txt
├── .env.example
├── alembic/                       # 数据库迁移
│   └── versions/
└── app/
    ├── core/
    │   ├── config.py              # Pydantic Settings，读取 .env
    │   ├── database.py            # AsyncSession + engine（asyncpg）
    │   ├── redis_client.py
    │   └── minio_client.py
    ├── models/                    # SQLAlchemy ORM（见 B-TASK-02）
    ├── schemas/                   # Pydantic 请求/响应 Schema
    ├── api/
    │   └── v1/
    │       ├── products.py
    │       ├── requirements.py
    │       ├── diagnosis.py
    │       ├── scene_map.py
    │       ├── generate.py        # SSE 流式端点
    │       ├── testcases.py
    │       ├── diff.py
    │       ├── knowledge.py
    │       ├── templates.py
    │       └── dashboard.py
    ├── services/                  # 业务逻辑（调用 engine）
    │   ├── requirement_service.py
    │   ├── diagnosis_service.py
    │   ├── generation_service.py
    │   ├── diff_service.py
    │   └── rag_service.py
    ├── engine/                    # 核心引擎层（纯算法，不依赖 FastAPI）
    │   ├── uda/                   # 通用文档抽象层
    │   │   ├── parser.py          # 统一入口
    │   │   ├── docx_parser.py     # Word 解析
    │   │   ├── pdf_parser.py      # PDF + OCR
    │   │   ├── md_parser.py       # Markdown 解析
    │   │   └── image_handler.py   # 图片归档 + OCR + Vision
    │   ├── diagnosis/
    │   │   ├── scanner.py         # 广度扫描（6类遗漏识别）
    │   │   ├── questioner.py      # 深度追问链（最多3层）
    │   │   └── checklist.py       # 行业必问清单（32条）
    │   ├── scene_map/
    │   │   └── generator.py       # 测试点草稿生成
    │   ├── case_generator.py      # 用例流式生成
    │   └── diff/
    │       ├── myers_diff.py      # 文本级 Myers Diff
    │       └── semantic_diff.py   # LLM 语义影响评估
    ├── rag/
    │   ├── embedder.py            # Qdrant 向量化
    │   └── retriever.py           # 检索
    └── tasks/                     # Celery 异步任务
        ├── parse_task.py
        └── embed_task.py
```

**main.py**：

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import products, requirements, diagnosis, scene_map, generate, testcases, diff, knowledge, templates, dashboard

app = FastAPI(title="Sisyphus-Y API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in [products, requirements, diagnosis, scene_map, generate, testcases, diff, knowledge, templates, dashboard]:
    app.include_router(router.router, prefix="/api/v1")
```

**requirements.txt（核心依赖）**：

```
fastapi==0.110.0
uvicorn[standard]==0.29.0
sqlalchemy[asyncio]==2.0.28
asyncpg==0.29.0
alembic==1.13.1
pydantic-settings==2.2.1
celery[redis]==5.3.6
redis==5.0.3
minio==7.2.7
python-docx==1.1.0
pypdf==4.1.0
PyMuPDF==1.24.0
paddleocr==2.7.3
paddlepaddle==2.6.1
Pillow==10.2.0
openai==1.13.3
langchain==0.1.12
langchain-openai==0.0.8
litellm==1.30.0
qdrant-client==1.8.0
python-multipart==0.0.9
httpx==0.27.0
difflib  # stdlib，无需安装
```

**.env.example**：

```
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/sisyphus_y
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=sisyphus-docs
QDRANT_URL=http://localhost:6333
OPENAI_API_KEY=sk-xxx
ANTHROPIC_API_KEY=sk-ant-xxx
DEFAULT_LLM_MODEL=gpt-4o
EMBEDDING_MODEL=text-embedding-3-small
```

---

### B-TASK-02 · 数据库模型（P0）

```python
# app/models/base.py
from sqlalchemy.orm import DeclarativeBase
import uuid
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import UUID

class Base(DeclarativeBase):
    pass

def gen_uuid():
    return str(uuid.uuid4())
```

```python
# app/models/product.py
class Product(Base):
    __tablename__ = "products"
    id          = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    name        = Column(String(100), nullable=False)
    description = Column(Text)
    icon        = Column(String(50))          # lucide 图标名，如 "Zap"
    color       = Column(String(20))          # 主题色（Tailwind 色名）
    created_at  = Column(DateTime, default=datetime.utcnow)
    iterations  = relationship("Iteration", back_populates="product", cascade="all, delete")
```

```python
# app/models/iteration.py
class Iteration(Base):
    __tablename__ = "iterations"
    id          = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    product_id  = Column(UUID(as_uuid=False), ForeignKey("products.id", ondelete="CASCADE"))
    name        = Column(String(100))          # "Sprint 2025-Q2"
    status      = Column(String(20), default="active")  # active / archived
    start_date  = Column(Date)
    end_date    = Column(Date)
    product     = relationship("Product", back_populates="iterations")
    requirements = relationship("Requirement", back_populates="iteration", cascade="all, delete")
```

```python
# app/models/requirement.py
class Requirement(Base):
    __tablename__ = "requirements"
    id             = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    iteration_id   = Column(UUID(as_uuid=False), ForeignKey("iterations.id", ondelete="CASCADE"))
    req_id         = Column(String(30), unique=True, nullable=False)  # "REQ-089"
    title          = Column(String(200), nullable=False)
    content_md     = Column(Text, default="")         # 用户编辑的 Markdown
    content_ast    = Column(JSONB, default=dict)      # UDA 解析后的 AST
    version        = Column(String(10), default="1.0")
    status         = Column(String(20), default="draft")  # draft/confirmed/archived
    priority       = Column(String(5), default="P1")
    assignee       = Column(String(50))
    reviewer       = Column(String(50))
    tags           = Column(ARRAY(String), default=list)
    created_at     = Column(DateTime, default=datetime.utcnow)
    updated_at     = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # Relations
    iteration      = relationship("Iteration", back_populates="requirements")
    versions       = relationship("RequirementVersion", back_populates="requirement", cascade="all, delete")
    scene_nodes    = relationship("SceneNode", back_populates="requirement", cascade="all, delete")
    test_cases     = relationship("TestCase", back_populates="requirement", cascade="all, delete")

class RequirementVersion(Base):
    __tablename__ = "requirement_versions"
    id             = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    requirement_id = Column(UUID(as_uuid=False), ForeignKey("requirements.id", ondelete="CASCADE"))
    version        = Column(String(10), nullable=False)
    content_md     = Column(Text)
    content_ast    = Column(JSONB)
    diff_from_prev = Column(JSONB)     # Myers diff 结果（可为空，首版无 diff）
    created_at     = Column(DateTime, default=datetime.utcnow)
    requirement    = relationship("Requirement", back_populates="versions")
```

```python
# app/models/scene_node.py
class SceneNode(Base):
    __tablename__ = "scene_nodes"
    id              = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    requirement_id  = Column(UUID(as_uuid=False), ForeignKey("requirements.id", ondelete="CASCADE"))
    node_id         = Column(String(20))    # "SN-001"
    title           = Column(String(200), nullable=False)
    description     = Column(Text)
    scenario_type   = Column(String(30))    # normal/exception/boundary/concurrent/permission
    source          = Column(String(20))    # document/ai_detected/user_added
    status          = Column(String(20), default="pending")  # covered/supplemented/missing/pending/confirmed
    estimated_cases = Column(Integer, default=3)
    parent_id       = Column(UUID(as_uuid=False), ForeignKey("scene_nodes.id"), nullable=True)
    sort_order      = Column(Integer, default=0)
    confirmed_at    = Column(DateTime, nullable=True)  # 非空 = 已锁定
    requirement     = relationship("Requirement", back_populates="scene_nodes")
    test_cases      = relationship("TestCase", back_populates="scene_node")
```

```python
# app/models/test_case.py
class TestCase(Base):
    __tablename__ = "test_cases"
    id               = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    requirement_id   = Column(UUID(as_uuid=False), ForeignKey("requirements.id", ondelete="CASCADE"))
    scene_node_id    = Column(UUID(as_uuid=False), ForeignKey("scene_nodes.id"), nullable=True)
    case_id          = Column(String(30), unique=True)  # "TC-089-001"
    title            = Column(String(300), nullable=False)
    priority         = Column(String(5), default="P1")
    case_type        = Column(String(30), default="normal")
    precondition     = Column(Text)
    # steps 存储格式：[{"step_num": 1, "action": "...", "expected_result": "..."}]
    steps            = Column(JSONB, default=list)
    status           = Column(String(20), default="draft")  # draft/reviewed/needs_rewrite/needs_review
    ai_generated     = Column(Boolean, default=True)
    quality_score    = Column(Float, nullable=True)   # 回流评分 0-5
    execution_result = Column(String(10), nullable=True)  # pass/fail/skip/blocked
    executed_at      = Column(DateTime, nullable=True)
    created_at       = Column(DateTime, default=datetime.utcnow)
    updated_at       = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    requirement      = relationship("Requirement", back_populates="test_cases")
    scene_node       = relationship("SceneNode", back_populates="test_cases")
```

```python
# app/models/knowledge.py
class KnowledgeDoc(Base):
    __tablename__ = "knowledge_docs"
    id             = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    name           = Column(String(200), nullable=False)
    doc_type       = Column(String(30))   # standard/guide/history_case/checklist/auto_archive
    chunk_count    = Column(Integer, default=0)
    indexed        = Column(Boolean, default=False)
    hit_count      = Column(Integer, default=0)
    minio_path     = Column(String(500))  # MinIO 原始文件路径
    auto_generated = Column(Boolean, default=False)  # 执行回流自动归档
    uploaded_at    = Column(DateTime, default=datetime.utcnow)

class Template(Base):
    __tablename__ = "templates"
    id             = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    name           = Column(String(100), nullable=False)
    description    = Column(Text)
    category       = Column(String(50))   # offline/realtime/data_asset/integration/quality/report
    icon           = Column(String(50))   # lucide 图标名
    is_official    = Column(Boolean, default=False)
    variables      = Column(JSONB, default=list)   # [{"key": "{{task_name}}", "label": "任务名称"}]
    # template_cases：[{"title": "{{task_name}}正常调度", "priority": "P0", "steps": [...]}]
    template_cases = Column(JSONB, default=list)
    use_count      = Column(Integer, default=0)
    estimated_cases = Column(Integer)
    created_at     = Column(DateTime, default=datetime.utcnow)
```

**Alembic 初始化命令**：

```bash
alembic init alembic
# 修改 alembic/env.py，import Base 并设置 target_metadata
alembic revision --autogenerate -m "init_all_tables"
alembic upgrade head
```

---

### B-TASK-03 · UDA 文档解析引擎（P0）

**核心原则**：所有格式统一转换为 DocumentAST，原始文件存 MinIO，内部只操作 AST。

#### DocumentAST 格式规范

```python
# 所有解析器的输出格式
DOCUMENT_AST = {
    "version": "1.0",
    "source_type": "docx",         # docx/pdf/md/txt
    "title": "需求标题",
    "sections": [
        {
            "type": "heading",     # heading/paragraph/list/table/image_ref/code
            "level": 1,            # heading 专用，1-6
            "content": "文本内容",
            "children": []         # 嵌套内容
        },
        {
            "type": "table",
            "rows": [["列1","列2"], ["值1","值2"]]
        },
        {
            "type": "image_ref",
            "minio_path": "requirements/req-089/img-abc123.png",
            "ocr_text": "OCR 提取的文字",
            "vision_desc": "GPT-4V 描述"
        }
    ],
    "metadata": {
        "word_count": 1200,
        "has_images": True,
        "is_scanned": False,
        "parsed_at": "2025-06-12T14:30:00Z"
    }
}
```

#### 统一解析入口

```python
# app/engine/uda/parser.py
from pathlib import Path
from typing import Union, Literal

SourceType = Literal["docx", "pdf", "md", "txt"]

class UDAParser:
    """通用文档抽象层 - 统一入口，所有格式都走这里"""

    def __init__(self, image_handler=None):
        self.image_handler = image_handler

    async def parse(self, file_bytes: bytes, source_type: SourceType) -> dict:
        if source_type == "docx":
            from .docx_parser import DocxParser
            raw = DocxParser().parse(file_bytes)
        elif source_type == "pdf":
            from .pdf_parser import PDFParser
            raw = PDFParser().parse(file_bytes)
        elif source_type in ("md", "txt"):
            from .md_parser import MarkdownParser
            raw = MarkdownParser().parse(file_bytes.decode("utf-8"))
        else:
            raise ValueError(f"不支持的文档类型: {source_type}")

        # 统一处理图片（下载外链 + 归档 MinIO + OCR）
        if self.image_handler and raw.get("images"):
            raw["sections"] = await self._process_images(raw, raw.pop("images", []))

        return self._to_ast(raw, source_type)

    def to_markdown(self, ast: dict) -> str:
        """AST → Markdown（用于 Diff 计算、LLM 输入）"""
        lines = []
        for section in ast.get("sections", []):
            if section["type"] == "heading":
                lines.append(f"{'#' * section['level']} {section['content']}\n")
            elif section["type"] == "paragraph":
                lines.append(f"{section['content']}\n")
            elif section["type"] == "table":
                for i, row in enumerate(section["rows"]):
                    lines.append("| " + " | ".join(row) + " |")
                    if i == 0:
                        lines.append("|" + "|".join(["---"] * len(row)) + "|")
            elif section["type"] == "image_ref":
                lines.append(f"\n[图片：{section.get('ocr_text', '')}]\n")
        return "\n".join(lines)

    def to_plain_text(self, ast: dict) -> str:
        """AST → 纯文本（用于向量化）"""
        parts = []
        for s in ast.get("sections", []):
            if s["type"] in ("heading", "paragraph"):
                parts.append(s["content"])
            elif s["type"] == "image_ref":
                if s.get("ocr_text"):
                    parts.append(s["ocr_text"])
                if s.get("vision_desc"):
                    parts.append(s["vision_desc"])
        return "\n".join(parts)
```

#### Word 文档解析器

```python
# app/engine/uda/docx_parser.py
import io
from docx import Document

class DocxParser:
    def parse(self, file_bytes: bytes) -> dict:
        doc = Document(io.BytesIO(file_bytes))
        sections = []
        images = []

        for para in doc.paragraphs:
            if not para.text.strip():
                continue

            style_name = para.style.name
            if style_name.startswith("Heading"):
                try:
                    level = int(style_name.split()[-1])
                except ValueError:
                    level = 1
                sections.append({
                    "type": "heading",
                    "level": level,
                    "content": para.text.strip()
                })
            else:
                # 提取 runs 中的格式信息
                runs_data = []
                for run in para.runs:
                    if run.text:
                        runs_data.append({
                            "text": run.text,
                            "bold": bool(run.bold),
                            "italic": bool(run.italic),
                        })
                sections.append({
                    "type": "paragraph",
                    "content": para.text.strip(),
                    "runs": runs_data
                })

        # 表格
        for table in doc.tables:
            rows = []
            for row in table.rows:
                rows.append([cell.text.strip() for cell in row.cells])
            if rows:
                sections.append({"type": "table", "rows": rows})

        # 嵌入图片
        import base64
        for rel in doc.part.rels.values():
            if "image" in rel.reltype:
                try:
                    blob = rel.target_part.blob
                    images.append({
                        "data": base64.b64encode(blob).decode(),
                        "content_type": rel.target_part.content_type,
                    })
                except Exception:
                    pass

        return {"sections": sections, "images": images}
```

#### PDF 解析器（含 PaddleOCR 扫描件支持）

```python
# app/engine/uda/pdf_parser.py
import io
import base64
import numpy as np
import pypdf
import fitz  # PyMuPDF

class PDFParser:
    _ocr = None  # 延迟初始化，避免启动时间过长

    def _get_ocr(self):
        if self._ocr is None:
            from paddleocr import PaddleOCR
            # 首次调用才初始化，使用 ch 中文模型
            self._ocr = PaddleOCR(use_angle_cls=True, lang="ch", show_log=False)
        return self._ocr

    def parse(self, file_bytes: bytes) -> dict:
        sections = []
        images = []

        # ── 阶段1：文字提取（优先直接提取，速度快且准确）──
        pdf_reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        total_pages = len(pdf_reader.pages)
        is_scanned = False

        for page_num, page in enumerate(pdf_reader.pages):
            text = page.extract_text() or ""
            text = text.strip()

            if len(text) < 30:
                # 文字太少，认为是扫描件，转 OCR
                is_scanned = True
                text = self._ocr_page(file_bytes, page_num)

            if text:
                # 简单按行拆分，尝试识别标题（全大写或短行）
                for line in text.split("\n"):
                    line = line.strip()
                    if not line:
                        continue
                    # 启发式：短行（<40字符）且不以标点结尾可能是标题
                    if len(line) < 40 and not line.endswith(("。", ".", ",", "，")):
                        sections.append({"type": "heading", "level": 2, "content": line})
                    else:
                        sections.append({"type": "paragraph", "content": line, "page": page_num + 1})

        # ── 阶段2：图片提取（PyMuPDF 更可靠）──
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        for page_num in range(len(doc)):
            page = doc[page_num]
            for img_info in page.get_images(full=True):
                xref = img_info[0]
                try:
                    base_image = doc.extract_image(xref)
                    images.append({
                        "data": base64.b64encode(base_image["image"]).decode(),
                        "content_type": f"image/{base_image['ext']}",
                        "page": page_num + 1
                    })
                except Exception:
                    pass
        doc.close()

        return {"sections": sections, "images": images, "is_scanned": is_scanned}

    def _ocr_page(self, file_bytes: bytes, page_num: int) -> str:
        """对单页执行 PaddleOCR，返回识别文字"""
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        page = doc[page_num]
        # 渲染为 300 DPI 图像
        mat = fitz.Matrix(300 / 72, 300 / 72)
        pix = page.get_pixmap(matrix=mat)
        img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
            pix.height, pix.width, pix.n if pix.n > 1 else 1
        )
        doc.close()

        ocr = self._get_ocr()
        result = ocr.ocr(img_array, cls=True)
        lines = []
        if result and result[0]:
            for line in result[0]:
                if line and len(line) >= 2:
                    text, confidence = line[1]
                    if confidence > 0.7:  # 过滤低置信度
                        lines.append(text)
        return "\n".join(lines)
```

#### 图片归档处理器

```python
# app/engine/uda/image_handler.py
import io
import hashlib
import base64
import httpx
from PIL import Image
import numpy as np

class ImageHandler:
    def __init__(self, minio_client, openai_client, bucket: str = "sisyphus-docs"):
        self.minio = minio_client
        self.openai = openai_client
        self.bucket = bucket

    async def process(
        self,
        req_id: str,
        image_data: bytes | None = None,
        url: str | None = None,
        run_vision: bool = True
    ) -> dict:
        """
        处理流程：
        1. URL → 下载（防止外链失效）
        2. 计算内容哈希，去重
        3. 上传 MinIO，返回内部路径
        4. PaddleOCR 文字提取
        5. GPT-4V 描述（仅大图，可选）
        """
        # 1. 获取图片数据
        if url and not image_data:
            async with httpx.AsyncClient(timeout=30) as client:
                try:
                    resp = await client.get(url)
                    resp.raise_for_status()
                    image_data = resp.content
                except Exception as e:
                    return {"error": f"下载失败: {e}", "minio_path": None}

        if not image_data:
            return {"error": "无图片数据", "minio_path": None}

        # 2. 内容哈希
        img_hash = hashlib.md5(image_data).hexdigest()[:12]
        ext = self._detect_ext(image_data)
        minio_path = f"requirements/{req_id}/img-{img_hash}.{ext}"

        # 3. 上传 MinIO（幂等，同 hash 不重复上传）
        try:
            self.minio.put_object(
                self.bucket, minio_path,
                io.BytesIO(image_data), len(image_data),
                content_type=f"image/{ext}"
            )
        except Exception:
            pass  # 已存在则忽略

        # 4. OCR
        ocr_text = self._run_ocr(image_data)

        # 5. GPT-4V（仅对 >10KB 的图片运行，大小图不值得）
        vision_desc = ""
        if run_vision and len(image_data) > 10_000:
            vision_desc = await self._run_vision(image_data)

        return {
            "minio_path": minio_path,
            "ocr_text": ocr_text,
            "vision_desc": vision_desc
        }

    def _detect_ext(self, data: bytes) -> str:
        """通过文件头魔数检测格式"""
        if data[:4] == b'\x89PNG':
            return "png"
        if data[:2] in (b'\xff\xd8',):
            return "jpg"
        if data[:4] == b'GIF8':
            return "gif"
        return "png"

    def _run_ocr(self, image_data: bytes) -> str:
        try:
            from paddleocr import PaddleOCR
            ocr = PaddleOCR(use_angle_cls=True, lang="ch", show_log=False)
            img = Image.open(io.BytesIO(image_data)).convert("RGB")
            result = ocr.ocr(np.array(img), cls=True)
            lines = []
            if result and result[0]:
                for line in result[0]:
                    if line and len(line) >= 2 and line[1][1] > 0.7:
                        lines.append(line[1][0])
            return "\n".join(lines)
        except Exception:
            return ""

    async def _run_vision(self, image_data: bytes) -> str:
        try:
            b64 = base64.b64encode(image_data).decode()
            resp = await self.openai.chat.completions.create(
                model="gpt-4o",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                        {"type": "text", "text": (
                            "这是来自需求文档的一张图片。"
                            "请用中文描述图片内容，重点说明：功能流程、数据结构、界面元素、或重要数字信息。"
                            "不超过150字。"
                        )}
                    ]
                }],
                max_tokens=200
            )
            return resp.choices[0].message.content or ""
        except Exception:
            return ""
```

---

### B-TASK-04 · 需求健康诊断引擎（P0）

#### 广度扫描器（6 类遗漏识别）

```python
# app/engine/diagnosis/scanner.py
import json, re
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

SCAN_SYSTEM = """你是一位专注于数据中台系统的资深测试工程师。你擅长从需求文档中识别测试遗漏。"""

SCAN_PROMPT = """请对以下需求文档进行测试场景遗漏扫描。

需求文档（Markdown 格式）：
{requirement_md}

请识别以下 6 类遗漏，每类最多 3 个，总计不超过 15 个：
1. 异常路径缺失：文档只描述成功路径，未说明失败/异常情况
2. 字段边界值缺失：数值/文本字段未说明最大值、最小值、空值处理
3. 权限场景缺失：未说明不同角色/权限下的行为差异
4. 并发/竞争条件缺失：多用户、高并发、分布式场景未说明
5. 数据状态流转缺失：状态机不完整，缺少某些状态转换路径
6. 关联功能影响：与其他模块的交互影响未说明

严格按 JSON 数组格式输出，不输出任何其他文字：
[
  {{
    "id": "GAP-001",
    "category": "异常路径缺失",
    "title": "网络中断时的处理策略未说明",
    "description": "§2 仅描述连接成功场景，未说明网络中断、超时时的重试和回滚策略",
    "risk_level": "high",
    "section_ref": "§2 数据源连接配置"
  }}
]"""

class RequirementScanner:
    def __init__(self, model: str = "gpt-4o"):
        self.llm = ChatOpenAI(model=model, temperature=0.1)

    async def scan(self, requirement_md: str) -> list[dict]:
        prompt = ChatPromptTemplate.from_messages([
            ("system", SCAN_SYSTEM),
            ("human", SCAN_PROMPT)
        ])
        chain = prompt | self.llm
        result = await chain.ainvoke({"requirement_md": requirement_md})

        # 安全提取 JSON（防止 LLM 输出多余文字）
        content = result.content
        match = re.search(r'\[.*\]', content, re.DOTALL)
        if not match:
            return []
        try:
            gaps = json.loads(match.group())
            return [g for g in gaps if isinstance(g, dict) and "title" in g]
        except json.JSONDecodeError:
            return []
```

#### 行业必问清单（32 条，6 大类）

```python
# app/engine/diagnosis/checklist.py
import json
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

INDUSTRY_CHECKLIST = {
    "idempotency": {
        "name": "幂等性",
        "items": [
            "重复提交/重复触发是否会产生重复数据？",
            "API 是否有幂等 Key 或去重机制？",
            "任务重试时是否保证幂等性？",
            "数据写入是否使用 upsert 而非 insert？",
            "消息队列消费者是否幂等？",
        ]
    },
    "timezone": {
        "name": "时区与时间",
        "items": [
            "系统是否统一使用 UTC 存储时间？",
            "展示层是否做时区转换（服务器时区 vs 用户时区）？",
            "跨时区的调度任务（如 cron）如何处理？",
            "时间戳字段是否使用 64 位整数或标准 ISO 格式？",
        ]
    },
    "large_data": {
        "name": "大数据量",
        "items": [
            "百万/千万级数据量时性能是否达标？",
            "是否有分页/游标机制，防止全量加载？",
            "批量操作是否有大小上限？超限如何处理？",
            "导出/下载大文件是否使用异步任务？",
            "索引是否覆盖高频查询字段？",
        ]
    },
    "state_machine": {
        "name": "状态流转",
        "items": [
            "所有可能的状态枚举是否完整？",
            "非法状态转换是否有防护（如：已归档 → 草稿）？",
            "状态变更是否记录操作日志（谁在什么时间改变了状态）？",
            "并发修改同一记录状态时是否有乐观锁？",
        ]
    },
    "consistency": {
        "name": "数据一致性",
        "items": [
            "分布式事务场景下如何保证数据一致性？",
            "事务边界是否清晰（哪些操作在同一事务内）？",
            "消息队列场景下如何处理消息丢失/重复？",
            "缓存与数据库的一致性如何保证？",
            "多节点写入时如何防止数据冲突？",
        ]
    },
    "permission": {
        "name": "权限与安全",
        "items": [
            "只读用户是否能调用写操作接口？",
            "数据是否有行/列级别的权限控制？",
            "敏感数据（手机号/身份证）是否有脱敏处理？",
            "API 是否有限流防刷机制？",
            "Token 过期/无效时返回码是否标准化（401 vs 403）？",
        ]
    }
}

COVERAGE_CHECK_PROMPT = """请判断以下需求文档中，是否已明确回答了这个问题。

需求文档（片段）：
{doc_snippet}

问题：{question}

只输出 JSON：{{"covered": true}} 或 {{"covered": false}}。
不输出其他内容。"""

class ChecklistEvaluator:
    def __init__(self, model: str = "gpt-4o"):
        self.llm = ChatOpenAI(model=model, temperature=0)

    async def evaluate(self, requirement_md: str) -> list[dict]:
        """返回文档中未覆盖的必问项"""
        # 截取文档前 3000 字供 LLM 判断（控制 token）
        doc_snippet = requirement_md[:3000]
        uncovered = []

        for category_key, category in INDUSTRY_CHECKLIST.items():
            for question in category["items"]:
                covered = await self._check(doc_snippet, question)
                if not covered:
                    uncovered.append({
                        "category": category["name"],
                        "question": question,
                        "risk_level": "medium"
                    })

        return uncovered

    async def _check(self, doc_snippet: str, question: str) -> bool:
        prompt = ChatPromptTemplate.from_template(COVERAGE_CHECK_PROMPT)
        chain = prompt | self.llm
        result = await chain.ainvoke({"doc_snippet": doc_snippet, "question": question})
        try:
            return json.loads(result.content).get("covered", False)
        except Exception:
            return False
```

#### 深度追问链（最多 3 层）

```python
# app/engine/diagnosis/questioner.py
import json
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

FOLLOWUP_PROMPT = """你是一位测试需求分析师，正在与产品经理确认需求细节。

当前遗漏项：
- 标题：{gap_title}
- 描述：{gap_description}

已有对话历史：
{history}

当前深度：第 {depth} 层（最多 3 层，请在第 3 层给出确认摘要并结束）

规则：
- 每次只问 1 个最关键的问题，问题简洁具体
- 问题聚焦于帮助编写测试用例所需的具体信息（阈值/状态/行为等）
- 如果用户回答已足够完整，提前结束
- 第 3 层必须结束，给出 confirmed_info 摘要

严格输出 JSON，不输出其他文字：
{{
  "question": "下一个问题（resolved=true 时为 null）",
  "resolved": false,
  "confirmed_info": "已确认的信息摘要（仅 resolved=true 时填写）"
}}"""

class DeepQuestioner:
    """三层终止深度追问链，每个 gap 独立 session"""

    def __init__(self, model: str = "gpt-4o"):
        self.llm = ChatOpenAI(model=model, temperature=0.2)
        # 内存中 session 存储（生产环境应存 Redis）
        self._sessions: dict[str, dict] = {}

    async def start(self, session_id: str, gap: dict) -> str:
        """初始化追问，返回第一个问题"""
        self._sessions[session_id] = {
            "gap": gap,
            "history": [],
            "depth": 1,
            "resolved": False
        }
        result = await self._generate(session_id)
        question = result.get("question", "")
        if question:
            self._sessions[session_id]["history"].append(
                {"role": "assistant", "content": question}
            )
        return question

    async def reply(self, session_id: str, user_answer: str) -> dict:
        """
        用户回答后生成下一问题。
        返回：{"next_question": str|None, "resolved": bool, "confirmed_info": str}
        """
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} 不存在")

        session["history"].append({"role": "user", "content": user_answer})
        session["depth"] += 1

        # 强制在第 3 层结束
        if session["depth"] > 3:
            return {
                "next_question": None,
                "resolved": True,
                "confirmed_info": "已达追问上限（3层），记录当前确认信息。"
            }

        result = await self._generate(session_id)
        if result.get("question") and not result.get("resolved"):
            session["history"].append(
                {"role": "assistant", "content": result["question"]}
            )
        session["resolved"] = result.get("resolved", False)

        return {
            "next_question": result.get("question"),
            "resolved": result.get("resolved", False),
            "confirmed_info": result.get("confirmed_info", "")
        }

    async def _generate(self, session_id: str) -> dict:
        session = self._sessions[session_id]
        prompt = ChatPromptTemplate.from_template(FOLLOWUP_PROMPT)
        chain = prompt | self.llm
        result = await chain.ainvoke({
            "gap_title": session["gap"]["title"],
            "gap_description": session["gap"]["description"],
            "history": json.dumps(session["history"], ensure_ascii=False),
            "depth": session["depth"]
        })
        try:
            return json.loads(result.content)
        except json.JSONDecodeError:
            return {"question": None, "resolved": True, "confirmed_info": result.content}
```

---

### B-TASK-05 · 场景地图生成（测试点分析）（P0）

```python
# app/engine/scene_map/generator.py
import json, re
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

SCENE_MAP_PROMPT = """你是测试架构专家，负责设计测试覆盖方案。

需求文档：
{requirement_md}

诊断补全信息（已与PM确认的遗漏项）：
{diagnosis_confirmed}

行业必问清单中未覆盖的项（需要补充测试点）：
{checklist_gaps}

请生成测试点列表（场景地图节点）。

粒度规范（非常重要）：
- 一个测试点对应 2~5 条用例
- ❌ 太粗：「验证数据同步功能正常」
- ❌ 太细：「验证输入 Host=192.168.1.100 时连接成功」
- ✅ 合适：「验证 MySQL/Oracle/PostgreSQL 数据源 JDBC 连接参数配置的有效性」

按场景类型分组，来源标注：
- document：需求文档中已明确说明
- ai_detected：AI 从文档中推断，或来自诊断补全
- user_added：来自行业必问清单补充

严格输出 JSON，不输出其他文字：
{{
  "nodes": [
    {{
      "id": "SN-001",
      "title": "测试点标题",
      "description": "详细描述，说明要验证什么",
      "scenario_type": "normal",
      "source": "document",
      "status": "covered",
      "estimated_cases": 3,
      "parent_id": null
    }}
  ],
  "summary": {{
    "total": 0,
    "covered": 0,
    "ai_detected": 0,
    "missing": 0,
    "pending": 0
  }}
}}

status 说明：
- covered：需求文档中已完整描述
- supplemented：AI 补全（诊断对话中已确认）
- missing：高风险遗漏，用户尚未确认
- pending：待用户确认"""

class SceneMapGenerator:
    def __init__(self, model: str = "gpt-4o"):
        self.llm = ChatOpenAI(model=model, temperature=0.1)

    async def generate(
        self,
        requirement_md: str,
        diagnosis_confirmed: list[dict],
        checklist_gaps: list[dict]
    ) -> dict:
        prompt = ChatPromptTemplate.from_template(SCENE_MAP_PROMPT)
        chain = prompt | self.llm
        result = await chain.ainvoke({
            "requirement_md": requirement_md,
            "diagnosis_confirmed": json.dumps(diagnosis_confirmed, ensure_ascii=False, indent=2),
            "checklist_gaps": json.dumps(checklist_gaps, ensure_ascii=False, indent=2)
        })

        content = result.content
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if not match:
            raise ValueError("LLM 返回格式错误，无法解析 JSON")
        return json.loads(match.group())
```

---

### B-TASK-06 · 测试用例流式生成（P0）

```python
# app/engine/case_generator.py
import json
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from typing import AsyncIterator

CASE_GEN_PROMPT = """你是测试用例编写专家，为数据中台系统生成测试用例。

需求摘要：
{requirement_summary}

当前测试点：
名称：{node_title}
描述：{node_desc}
场景类型：{scenario_type}
需要生成：{estimated_cases} 条用例

知识库相关规范（供参考）：
{rag_context}

要求：
1. 严格在测试点描述范围内生成，不扩展到其他测试点
2. 优先级分配：P0（核心必须验证）> P1（重要场景）> P2（边界补充）
3. 步骤清晰可操作，预期结果具体可验证
4. 前置条件说明系统环境和数据准备

对每条用例，输出一个独立的 JSON 对象（在同一次响应中逐个输出）：
{{
  "id": "TC-{req_short_id}-{seq}",
  "title": "用例标题",
  "priority": "P0",
  "case_type": "{scenario_type}",
  "precondition": "前置条件",
  "steps": [
    {{"step_num": 1, "action": "操作步骤", "expected_result": "预期结果（建议放在最后一步）"}}
  ],
  "source_node_id": "{node_id}",
  "source_node_title": "{node_title}",
  "ai_generated": true
}}
---（每条用例之间用三条横线分隔）"""

class CaseGenerator:
    def __init__(self, model: str = "gpt-4o"):
        self.llm = ChatOpenAI(model=model, temperature=0.3, streaming=True)

    async def stream_generate(
        self,
        requirement_summary: str,
        scene_node: dict,
        rag_context: str = "",
    ) -> AsyncIterator[dict]:
        """
        流式生成用例，每次 yield 一个事件：
        {"type": "chunk", "content": "..."} — 文本片段
        {"type": "case_done", "case": {...}} — 一条完整用例
        {"type": "node_done"} — 当前测试点所有用例生成完毕
        """
        prompt = ChatPromptTemplate.from_template(CASE_GEN_PROMPT)
        messages = prompt.format_messages(
            requirement_summary=requirement_summary,
            node_title=scene_node["title"],
            node_desc=scene_node["description"],
            scenario_type=scene_node["scenario_type"],
            estimated_cases=scene_node.get("estimated_cases", 3),
            rag_context=rag_context or "（无相关规范）",
            req_short_id=scene_node.get("req_short_id", "XXX"),
            seq="001",
            node_id=scene_node["id"]
        )

        buffer = ""
        async for chunk in self.llm.astream(messages):
            text = chunk.content
            buffer += text
            yield {"type": "chunk", "content": text}

            # 检测完整用例分隔符
            while "---" in buffer:
                parts = buffer.split("---", 1)
                case_text = parts[0].strip()
                buffer = parts[1]

                if case_text:
                    case = self._parse_case(case_text)
                    if case:
                        yield {"type": "case_done", "case": case}

        # 处理最后一条（无分隔符结尾）
        if buffer.strip():
            case = self._parse_case(buffer.strip())
            if case:
                yield {"type": "case_done", "case": case}

        yield {"type": "node_done"}

    def _parse_case(self, text: str) -> dict | None:
        import re
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if not match:
            return None
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            return None
```

**SSE 端点**：

```python
# app/api/v1/generate.py
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json

router = APIRouter(prefix="/generate", tags=["generate"])

class GenerateRequest(BaseModel):
    requirement_id: str
    scene_node_ids: list[str]  # 要生成的测试点 ID 列表

@router.post("/stream")
async def generate_stream(req: GenerateRequest, db=Depends(get_db)):
    """
    SSE 流式生成测试用例
    前端通过 fetch + ReadableStream 接收

    事件格式（每行一个 JSON）：
    data: {"type": "node_start", "node_id": "...", "node_title": "..."}
    data: {"type": "chunk", "content": "..."}
    data: {"type": "case_done", "case": {...}}
    data: {"type": "node_done"}
    data: {"type": "all_done", "total": N}
    """
    async def event_generator():
        generator = CaseGenerator()
        rag = KnowledgeRetriever()
        total_cases = 0

        requirement = await get_requirement(req.requirement_id, db)
        req_summary = UDAParser().to_plain_text(requirement.content_ast)[:2000]

        for node_id in req.scene_node_ids:
            node = await get_scene_node(node_id, db)
            rag_context = await rag.retrieve(node["description"], top_k=3)
            rag_text = "\n---\n".join([r["text"] for r in rag_context])

            yield f"data: {json.dumps({'type': 'node_start', 'node_id': node_id, 'node_title': node['title']}, ensure_ascii=False)}\n\n"

            async for event in generator.stream_generate(req_summary, node, rag_text):
                if event["type"] == "case_done":
                    # 保存到数据库
                    await save_test_case(event["case"], requirement.id, db)
                    total_cases += 1
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

        yield f"data: {json.dumps({'type': 'all_done', 'total': total_cases})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"  # 禁用 nginx 缓冲
        }
    )
```

---

### B-TASK-07 · Diff 引擎（P0）

```python
# app/engine/diff/myers_diff.py
import difflib
import re

class RequirementDiffEngine:
    def compute(self, old_md: str, new_md: str) -> dict:
        """
        Myers 算法（difflib.unified_diff）计算文本级 Diff
        返回结构化 hunks
        """
        old_lines = old_md.splitlines()
        new_lines = new_md.splitlines()

        diff_lines = list(difflib.unified_diff(
            old_lines, new_lines,
            fromfile="v_old", tofile="v_new", lineterm=""
        ))

        hunks = []
        current_hunk = None
        del_count = 0
        add_count = 0

        for line in diff_lines:
            if line.startswith("@@"):
                if current_hunk:
                    hunks.append(current_hunk)
                # 提取章节上下文（@@ -N,M +N,M @@ 章节标题）
                section_match = re.search(r'@@ .+ @@ (.+)', line)
                section_title = section_match.group(1) if section_match else ""
                current_hunk = {"section": section_title, "lines": []}
            elif current_hunk is not None:
                if line.startswith("-"):
                    current_hunk["lines"].append({"type": "del", "content": line[1:]})
                    del_count += 1
                elif line.startswith("+"):
                    current_hunk["lines"].append({"type": "add", "content": line[1:]})
                    add_count += 1
                elif not line.startswith(("---", "+++")):
                    current_hunk["lines"].append({"type": "ctx", "content": line[1:]})

        if current_hunk:
            hunks.append(current_hunk)

        return {
            "hunks": hunks,
            "del_count": del_count,
            "add_count": add_count,
            "changed": del_count > 0 or add_count > 0
        }
```

```python
# app/engine/diff/semantic_diff.py
import json, re
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

IMPACT_PROMPT = """你是一位测试影响分析专家。

需求文档变更摘要：
{diff_summary}

已有测试用例列表（ID + 标题 + 关联测试点）：
{cases_summary}

请分析每条用例受本次变更的影响，输出影响等级：
- needs_rewrite：用例核心逻辑需要完全重写
- needs_review：可能受影响，需人工确认
- no_impact：不受影响

同时给出新增测试点建议（针对变更中的新功能）。

严格输出 JSON：
{{
  "impacts": [
    {{"case_id": "TC-089-001", "level": "needs_rewrite", "reason": "变更了超时时间，步骤中的等待时间断言需更新"}}
  ],
  "new_test_points": [
    {{"title": "自定义超时阈值验证", "description": "新增用户可配置超时时间功能"}}
  ],
  "summary": "本次变更主要影响连接超时相关测试..."
}}"""

class SemanticImpactAnalyzer:
    def __init__(self, model: str = "gpt-4o"):
        self.llm = ChatOpenAI(model=model, temperature=0.1)

    async def analyze(self, diff_result: dict, test_cases: list[dict]) -> dict:
        diff_summary = self._summarize_diff(diff_result)
        cases_summary = "\n".join([
            f"- {c['case_id']}: {c['title']} (测试点: {c.get('scene_node_title','')})"
            for c in test_cases[:50]  # 最多 50 条防止超 token
        ])

        prompt = ChatPromptTemplate.from_template(IMPACT_PROMPT)
        chain = prompt | self.llm
        result = await chain.ainvoke({
            "diff_summary": diff_summary,
            "cases_summary": cases_summary
        })

        match = re.search(r'\{.*\}', result.content, re.DOTALL)
        if not match:
            return {"impacts": [], "new_test_points": [], "summary": ""}
        return json.loads(match.group())

    def _summarize_diff(self, diff_result: dict) -> str:
        lines = []
        for hunk in diff_result["hunks"]:
            if hunk["section"]:
                lines.append(f"\n[{hunk['section']}]")
            for line in hunk["lines"]:
                if line["type"] == "del":
                    lines.append(f"  - 删除：{line['content']}")
                elif line["type"] == "add":
                    lines.append(f"  + 新增：{line['content']}")
        return "\n".join(lines)
```

---

### B-TASK-08 · RAG 知识库引擎（P1）

```python
# app/rag/embedder.py
import uuid
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
from langchain_openai import OpenAIEmbeddings
from app.core.config import settings

class KnowledgeEmbedder:
    COLLECTION = "sisyphus_knowledge"
    VECTOR_SIZE = 1536  # text-embedding-3-small

    def __init__(self):
        self.qdrant = QdrantClient(url=settings.QDRANT_URL)
        self.embeddings = OpenAIEmbeddings(model=settings.EMBEDDING_MODEL)
        self._ensure_collection()

    def _ensure_collection(self):
        existing = [c.name for c in self.qdrant.get_collections().collections]
        if self.COLLECTION not in existing:
            self.qdrant.create_collection(
                self.COLLECTION,
                vectors_config=VectorParams(size=self.VECTOR_SIZE, distance=Distance.COSINE)
            )

    async def embed_chunks(self, doc_id: str, doc_type: str, chunks: list[dict]):
        """
        chunks: [{"chunk_id": "...", "text": "...", "page_num": 1}]
        """
        texts = [c["text"] for c in chunks]
        vectors = await self.embeddings.aembed_documents(texts)

        points = [
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vec,
                payload={
                    "doc_id": doc_id,
                    "doc_type": doc_type,
                    "chunk_id": chunk["chunk_id"],
                    "text": chunk["text"],
                    "page_num": chunk.get("page_num", 0)
                }
            )
            for vec, chunk in zip(vectors, chunks)
        ]
        self.qdrant.upsert(collection_name=self.COLLECTION, points=points)
        return len(points)

    async def delete_doc(self, doc_id: str):
        """删除某文档的所有向量"""
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        self.qdrant.delete(
            collection_name=self.COLLECTION,
            points_selector=Filter(
                must=[FieldCondition(key="doc_id", match=MatchValue(value=doc_id))]
            )
        )
```

```python
# app/rag/retriever.py
from qdrant_client.models import Filter, FieldCondition, MatchValue
from app.rag.embedder import KnowledgeEmbedder

class KnowledgeRetriever:
    def __init__(self, embedder: KnowledgeEmbedder | None = None):
        self.embedder = embedder or KnowledgeEmbedder()

    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        doc_type: str | None = None,
        score_threshold: float = 0.72
    ) -> list[dict]:
        """
        检索最相关的知识片段
        doc_type 可过滤特定类型的知识库（如只查标准文档）
        """
        query_vector = await self.embedder.embeddings.aembed_query(query)

        query_filter = None
        if doc_type:
            query_filter = Filter(
                must=[FieldCondition(key="doc_type", match=MatchValue(value=doc_type))]
            )

        results = self.embedder.qdrant.search(
            collection_name=KnowledgeEmbedder.COLLECTION,
            query_vector=query_vector,
            query_filter=query_filter,
            limit=top_k,
            score_threshold=score_threshold
        )

        return [
            {
                "text": r.payload["text"],
                "doc_id": r.payload["doc_id"],
                "doc_type": r.payload.get("doc_type", ""),
                "chunk_id": r.payload["chunk_id"],
                "similarity": round(r.score, 4)
            }
            for r in results
        ]
```

---

### B-TASK-09 · 完整 API 路由清单（P0）

```
# 子产品 / 迭代 / 需求管理
GET    /api/v1/products
POST   /api/v1/products
GET    /api/v1/products/{id}/iterations
POST   /api/v1/products/{id}/iterations
GET    /api/v1/iterations/{id}/requirements
POST   /api/v1/requirements
GET    /api/v1/requirements/{id}
PATCH  /api/v1/requirements/{id}          # 更新时自动创建版本快照
POST   /api/v1/requirements/{id}/confirm  # 锁定需求，可触发诊断
GET    /api/v1/requirements/{id}/versions

# 文档解析（UDA）
POST   /api/v1/parse/upload               # 上传文件 → Celery 异步解析，返回 task_id
GET    /api/v1/parse/status/{task_id}     # 查询解析进度
POST   /api/v1/parse/text                 # 直接提交 Markdown 文本

# 需求健康诊断
POST   /api/v1/requirements/{id}/diagnose              # 触发广度扫描，返回 diagnosis_id
GET    /api/v1/diagnosis/{id}                          # 获取完整诊断报告（扫描结果+清单结果）
POST   /api/v1/diagnosis/{id}/session/start            # 开始追问对话
POST   /api/v1/diagnosis/{id}/session/{sid}/reply      # 用户回答

# 场景地图 / 测试点
POST   /api/v1/requirements/{id}/scene-map/generate    # AI 生成测试点草稿
GET    /api/v1/requirements/{id}/scene-map             # 获取测试点列表和汇总
PATCH  /api/v1/scene-nodes/{node_id}                   # 编辑单个测试点
DELETE /api/v1/scene-nodes/{node_id}
POST   /api/v1/requirements/{id}/scene-map/confirm     # 用户确认所有测试点（设置 confirmed_at）
POST   /api/v1/requirements/{id}/scene-map/export      # 导出（json/md/png）

# 测试用例生成（SSE 流式）
POST   /api/v1/generate/stream             # 主流式端点（EventStream）
POST   /api/v1/generate/from-template     # 模板驱动生成（非流式）

# 测试用例管理
GET    /api/v1/requirements/{id}/testcases   # 支持 priority/case_type/status 筛选
GET    /api/v1/testcases/{id}
PATCH  /api/v1/testcases/{id}
DELETE /api/v1/testcases/{id}
POST   /api/v1/testcases/{id}/execution      # 回流执行结果
POST   /api/v1/testcases/export             # 批量导出（xlsx/xmind/csv）

# Diff & 变更分析
POST   /api/v1/requirements/{id}/diff        # 计算两版本 Diff（Myers + LLM 语义）
GET    /api/v1/requirements/{id}/diff/latest # 最新变更影响报告（含受影响用例列表）
POST   /api/v1/requirements/{id}/diff/rerun  # 重新生成受影响用例

# 覆盖矩阵
GET    /api/v1/iterations/{id}/coverage-matrix

# 知识库
GET    /api/v1/knowledge
POST   /api/v1/knowledge/upload              # 上传 → Celery 异步向量化
DELETE /api/v1/knowledge/{id}
POST   /api/v1/knowledge/{id}/reindex        # 重建向量索引
POST   /api/v1/knowledge/test               # RAG 命中率测试（输入查询返回 top-k）

# 模板库
GET    /api/v1/templates
POST   /api/v1/templates
GET    /api/v1/templates/{id}
POST   /api/v1/templates/{id}/use           # 变量替换后批量生成用例

# 质量看板
GET    /api/v1/dashboard/overview
GET    /api/v1/dashboard/coverage-trend      # 按迭代的覆盖率趋势
GET    /api/v1/dashboard/quality-distribution
GET    /api/v1/dashboard/recent-activity
```

---

### B-TASK-10 · Celery 异步任务（P1）

```python
# app/tasks/parse_task.py
from celery import Celery
from app.core.config import settings

celery_app = Celery("sisyphus_y", broker=settings.CELERY_BROKER_URL)

@celery_app.task(bind=True, max_retries=3, default_retry_delay=5)
def parse_document_task(self, minio_path: str, doc_type: str, requirement_id: str):
    """
    异步文档解析流程：
    1. 从 MinIO 读取原始文件
    2. UDAParser 解析为 AST
    3. ImageHandler 处理所有图片（下载外链 + OCR + Vision）
    4. 更新 Requirement.content_ast
    5. 触发向量化任务
    """
    import asyncio
    try:
        asyncio.run(_parse_and_save(minio_path, doc_type, requirement_id))
        embed_task.delay(requirement_id)
    except Exception as exc:
        raise self.retry(exc=exc)

@celery_app.task
def embed_task(requirement_id: str):
    """将需求 AST 内容向量化，存入 Qdrant（供 RAG 检索）"""
    import asyncio
    asyncio.run(_embed_requirement(requirement_id))
```

---

## 七、任务优先级与顺序

| 序号 | 任务                                                 | 类型 | 优先级 | 预估工时 |
| ---- | ---------------------------------------------------- | ---- | ------ | -------- |
| 1    | Tailwind 主题配置 + shadcn/ui 安装 + lucide 图标替换 | 前端 | **P0** | 2h       |
| 2    | B-TASK-01 后端工程初始化（FastAPI + 目录 + .env）    | 后端 | **P0** | 2h       |
| 3    | B-TASK-02 数据库模型 + Alembic 迁移                  | 后端 | **P0** | 3h       |
| 4    | **F-TASK-01 生成工作台 CaseCard 修复（最紧急）**     | 前端 | **P0** | 4h       |
| 5    | B-TASK-06 用例流式生成 SSE 端点                      | 后端 | **P0** | 4h       |
| 6    | B-TASK-03 UDA 解析引擎（docx+pdf+图片归档）          | 后端 | **P0** | 8h       |
| 7    | F-TASK-02 项目列表页                                 | 前端 | **P0** | 3h       |
| 8    | F-TASK-03 需求卡片编辑器                             | 前端 | **P0** | 4h       |
| 9    | B-TASK-04 需求健康诊断引擎（扫描+追问+清单）         | 后端 | **P0** | 7h       |
| 10   | F-TASK-04 健康诊断页面                               | 前端 | **P0** | 5h       |
| 11   | B-TASK-05 场景地图生成                               | 后端 | **P0** | 3h       |
| 12   | F-TASK-05 测试点确认页面 + React Flow                | 前端 | **P0** | 5h       |
| 13   | F-TASK-06 用例管理                                   | 前端 | P1     | 3h       |
| 14   | B-TASK-07 Diff 引擎（Myers + LLM 语义）              | 后端 | P1     | 4h       |
| 15   | F-TASK-07 Diff 视图                                  | 前端 | P1     | 3h       |
| 16   | B-TASK-08 RAG 知识库引擎                             | 后端 | P1     | 5h       |
| 17   | F-TASK-08 质量看板（Recharts）                       | 前端 | P1     | 3h       |
| 18   | F-TASK-09 知识库页面                                 | 前端 | P1     | 2h       |
| 19   | F-TASK-10 模板库页面                                 | 前端 | P1     | 2h       |
| 20   | F-TASK-11 系统设置                                   | 前端 | P1     | 2h       |
| 21   | B-TASK-10 Celery 异步任务 + B-TASK-09 API 全联调     | 全栈 | P1     | 8h       |

---

## 八、验收标准

### 前端全局

- [ ] 所有颜色来自 Tailwind 自定义 token（`text-sy-accent` 等），无 `style={{ color: '#xxx' }}` 硬编码
- [ ] 所有图标来自 lucide-react，项目中不出现 emoji 作为 UI 元素
- [ ] 三种字体（DM Sans / JetBrains Mono / Syne）按规范应用
- [ ] 全站深色背景（`bg-sy-bg`），无白色背景页面
- [ ] 所有 Button / Input / Badge / Switch 使用 shadcn/ui 组件

### 生成工作台（最高优先）

- [ ] **中间区域不出现任何 JSON 字符串文本**
- [ ] 每条用例完整渲染：ID、优先级 Badge、类型 Badge、标题、前置条件、步骤列表（逐条编号）、预期结果（accent 色）
- [ ] 生成中显示 `<Loader2 animate-spin />` StatusBadge，完成后变 `<CheckCircle2 />` success
- [ ] 右栏用例列表实时同步，激活项有 `bg-sy-accent/10` 背景
- [ ] 三栏各自独立滚动，不超出视口高度

### 后端引擎

- [ ] docx / pdf（含扫描件）/ md 三种格式均能解析为 DocumentAST
- [ ] 扫描件 PDF 能通过 PaddleOCR 提取文字（置信度 > 0.7 的行）
- [ ] 需求文档图片能下载归档到 MinIO，返回 `minio_path` 内部路径
- [ ] 广度扫描能识别至少 6 类遗漏并返回 JSON 数组
- [ ] 追问链在第 3 层后强制终止，返回 `resolved: true`
- [ ] SSE 流式端点能逐步推送 `case_done` 事件，前端实时渲染
- [ ] Diff 引擎能识别新增行（`add`）/ 删除行（`del`）并返回 hunks

### 对照原型验收

- [ ] 打开 `Sisyphus-Y.html` 并排对比，颜色/字体/间距视觉差异 < 5%
- [ ] 不接受"结构对了但颜色不对"
