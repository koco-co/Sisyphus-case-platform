# TestGen Pro 阶段一实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 实现 TestGen Pro 核心主流程——项目列表、需求卡片、健康诊断、测试点确认、生成工作台、用例管理共 6 个页面，打通「需求→诊断→测试点→用例生成」完整链路。

**Architecture:** 后端 FastAPI + SQLAlchemy async DDD 模块化，新增 M03/M04/M05/M06 四个模块；前端 Next.js 16 App Router + React Query + Zustand，深色主题设计系统；AI 流式输出通过 SSE 实现，思考过程与内容分事件类型传输。

**Tech Stack:** Python 3.12 / FastAPI / SQLAlchemy 2 / LangChain 0.3 / Next.js 16 / React 19 / Antd 6 / Tailwind 4 / Zustand 5 / React Query 5

---

## 约定与参考

- 后端模块结构参考 `backend/app/modules/products/`（router/models/schemas/service 四文件）
- `BaseModel` 提供 UUID 主键 + 时间戳 + `deleted_at` 软删除，所有新表继承
- `BaseSchema` / `BaseResponse` 提供 Pydantic 基类，`from_attributes=True`
- `AsyncSessionDep` 在 router 中注入 `AsyncSession`
- 软删除查询必须加 `.where(Model.deleted_at.is_(None))`
- 前端 API 调用用 `src/lib/api-client.ts` 的 `apiClient<T>()` 函数
- Python lint: `cd backend && uv run ruff check . && uv run ruff format .`
- 前端 lint: `cd frontend && bunx biome check --write .`

---

## Task 1: 设计系统 — CSS 变量与全局主题

**Files:**
- Modify: `frontend/src/app/globals.css`
- Modify: `frontend/src/app/layout.tsx`

**Step 1: 替换 globals.css 为深色主题 token**

```css
/* frontend/src/app/globals.css */
@import "tailwindcss";
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500;600&family=Syne:wght@600;700;800&display=swap');

@layer base {
  :root {
    --bg:       #0d0f12;
    --bg1:      #131619;
    --bg2:      #1a1e24;
    --bg3:      #212730;
    --border:   #2a313d;
    --border2:  #353d4a;
    --text:     #e2e8f0;
    --text2:    #94a3b8;
    --text3:    #566577;
    --accent:   #00d9a3;
    --accent2:  #00b386;
    --accent-d: rgba(0, 217, 163, 0.1);
    --amber:    #f59e0b;
    --red:      #f43f5e;
    --blue:     #3b82f6;
    --purple:   #a855f7;
  }
}

@theme inline {
  --color-bg:      var(--bg);
  --color-bg1:     var(--bg1);
  --color-bg2:     var(--bg2);
  --color-bg3:     var(--bg3);
  --color-accent:  var(--accent);
  --color-accent2: var(--accent2);
  --color-text:    var(--text);
  --color-text2:   var(--text2);
  --color-text3:   var(--text3);
  --color-amber:   var(--amber);
  --color-red:     var(--red);
  --color-blue:    var(--blue);
  --color-border:  var(--border);
  --font-sans:     'DM Sans', sans-serif;
  --font-mono:     'JetBrains Mono', monospace;
  --font-display:  'Syne', sans-serif;
}

* { box-sizing: border-box; }

body {
  background: var(--bg);
  color: var(--text);
  font-family: var(--font-sans);
  font-size: 13px;
  line-height: 1.5;
}

/* 滚动条样式 */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--bg2); }
::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 3px; }
```

**Step 2: 更新 layout.tsx，移除 Geist 字体，加入 AntD ConfigProvider**

```tsx
// frontend/src/app/layout.tsx
import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'TestGen Pro',
  description: 'AI-driven test case generation platform',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
```

**Step 3: 创建 AntD 主题 Provider**

```tsx
// frontend/src/components/providers/AntdProvider.tsx
'use client';
import { ConfigProvider, App } from 'antd';
import zhCN from 'antd/locale/zh_CN';

const theme = {
  token: {
    colorPrimary: '#00d9a3',
    colorBgBase: '#0d0f12',
    colorTextBase: '#e2e8f0',
    colorBorder: '#2a313d',
    colorBgContainer: '#131619',
    colorBgElevated: '#1a1e24',
    borderRadius: 6,
    fontFamily: "'DM Sans', sans-serif",
  },
  components: {
    Table: { colorBgContainer: '#131619' },
    Modal: { contentBg: '#131619' },
    Drawer: { colorBgElevated: '#131619' },
  },
};

export function AntdProvider({ children }: { children: React.ReactNode }) {
  return (
    <ConfigProvider theme={theme} locale={zhCN}>
      <App>{children}</App>
    </ConfigProvider>
  );
}
```

**Step 4: 创建 React Query Provider**

```tsx
// frontend/src/components/providers/QueryProvider.tsx
'use client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useState } from 'react';

export function QueryProvider({ children }: { children: React.ReactNode }) {
  const [client] = useState(() => new QueryClient({
    defaultOptions: { queries: { staleTime: 30_000, retry: 1 } },
  }));
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}
```

**Step 5: 组合到根 layout**

```tsx
// frontend/src/app/layout.tsx (最终版)
import type { Metadata } from 'next';
import { AntdProvider } from '@/components/providers/AntdProvider';
import { QueryProvider } from '@/components/providers/QueryProvider';
import './globals.css';

export const metadata: Metadata = { title: 'TestGen Pro' };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>
        <QueryProvider>
          <AntdProvider>{children}</AntdProvider>
        </QueryProvider>
      </body>
    </html>
  );
}
```

**Step 6: 验证前端能启动**

```bash
cd frontend && bun dev
# 访问 http://localhost:3000，页面背景应为 #0d0f12 深色
```

**Step 7: Commit**

```bash
git add frontend/src/
git commit -m "feat(frontend): add dark theme design system and providers"
```

---

## Task 2: UI 基础组件库

**Files:**
- Create: `frontend/src/components/ui/StatusPill.tsx`
- Create: `frontend/src/components/ui/StatCard.tsx`
- Create: `frontend/src/components/ui/SidebarNav.tsx`
- Create: `frontend/src/components/ui/ProgressBar.tsx`
- Create: `frontend/src/components/ui/ProgressSteps.tsx`
- Create: `frontend/src/components/ui/index.ts`

**Step 1: StatusPill 组件**

```tsx
// frontend/src/components/ui/StatusPill.tsx
type PillVariant = 'green' | 'amber' | 'red' | 'blue' | 'purple' | 'gray';

const variantStyles: Record<PillVariant, string> = {
  green:  'bg-[rgba(0,217,163,0.12)] text-accent border border-[rgba(0,217,163,0.25)]',
  amber:  'bg-[rgba(245,158,11,0.1)] text-amber border border-[rgba(245,158,11,0.25)]',
  red:    'bg-[rgba(244,63,94,0.1)] text-red border border-[rgba(244,63,94,0.25)]',
  blue:   'bg-[rgba(59,130,246,0.1)] text-blue border border-[rgba(59,130,246,0.25)]',
  purple: 'bg-[rgba(168,85,247,0.1)] text-purple border border-[rgba(168,85,247,0.25)]',
  gray:   'bg-bg3 text-text3 border border-border',
};

interface StatusPillProps {
  variant: PillVariant;
  children: React.ReactNode;
}

export function StatusPill({ variant, children }: StatusPillProps) {
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium font-mono ${variantStyles[variant]}`}>
      {children}
    </span>
  );
}
```

**Step 2: StatCard 组件**

```tsx
// frontend/src/components/ui/StatCard.tsx
interface StatCardProps {
  value: string | number;
  label: string;
  delta?: string;
  deltaColor?: string;
  progress?: number; // 0-100
  highlighted?: boolean;
}

export function StatCard({ value, label, delta, deltaColor = 'text-accent', progress, highlighted }: StatCardProps) {
  return (
    <div className={`bg-bg1 border border-border rounded-[10px] p-4 ${highlighted ? 'border-[rgba(0,217,163,0.25)] bg-[rgba(0,217,163,0.04)]' : ''}`}>
      <div className={`font-mono text-[26px] font-semibold leading-none ${highlighted ? 'text-accent' : 'text-text'}`}>
        {value}
      </div>
      <div className="text-[11.5px] text-text3 mt-1">{label}</div>
      {delta && <div className={`font-mono text-[11px] mt-2 ${deltaColor}`}>{delta}</div>}
      {progress !== undefined && (
        <div className="h-[3px] bg-bg3 rounded-sm overflow-hidden mt-1.5">
          <div className="h-full bg-accent rounded-sm" style={{ width: `${progress}%` }} />
        </div>
      )}
    </div>
  );
}
```

**Step 3: SidebarNav 组件**

```tsx
// frontend/src/components/ui/SidebarNav.tsx
interface SidebarItemProps {
  icon?: string;
  label: string;
  count?: number;
  active?: boolean;
  onClick?: () => void;
}

export function SidebarItem({ icon, label, count, active, onClick }: SidebarItemProps) {
  return (
    <div
      onClick={onClick}
      className={`flex items-center gap-2 px-2 py-1.5 rounded-md cursor-pointer text-[12.5px] transition-all border ${
        active
          ? 'bg-accent-d text-accent border-[rgba(0,217,163,0.2)]'
          : 'text-text2 border-transparent hover:bg-bg2 hover:text-text'
      }`}
    >
      {icon && <span className="text-[14px] w-[18px] text-center opacity-80">{icon}</span>}
      <span className="flex-1">{label}</span>
      {count !== undefined && (
        <span className="font-mono text-[10px] text-text3">{count}</span>
      )}
    </div>
  );
}

interface SidebarSectionProps {
  label: string;
  children: React.ReactNode;
}

export function SidebarSection({ label, children }: SidebarSectionProps) {
  return (
    <div className="px-3 pb-2">
      <div className="text-[10px] font-semibold text-text3 uppercase tracking-[1.2px] px-1 mb-1.5">{label}</div>
      {children}
    </div>
  );
}
```

**Step 4: ProgressBar 和 ProgressSteps**

```tsx
// frontend/src/components/ui/ProgressBar.tsx
interface ProgressBarProps {
  value: number; // 0-100
  variant?: 'accent' | 'amber' | 'red';
  height?: number;
}

export function ProgressBar({ value, variant = 'accent', height = 3 }: ProgressBarProps) {
  const colorMap = { accent: 'bg-accent', amber: 'bg-amber', red: 'bg-red' };
  return (
    <div className="bg-bg3 rounded-sm overflow-hidden" style={{ height }}>
      <div className={`h-full rounded-sm transition-all ${colorMap[variant]}`} style={{ width: `${value}%` }} />
    </div>
  );
}
```

```tsx
// frontend/src/components/ui/ProgressSteps.tsx
interface Step { label: string; status: 'done' | 'active' | 'pending'; }

export function ProgressSteps({ steps }: { steps: Step[] }) {
  return (
    <div className="flex items-center mb-5">
      {steps.map((step, i) => (
        <div key={i} className="flex items-center">
          <div className={`flex items-center gap-1.5 px-3.5 py-1.5 text-[12px] font-medium rounded-md ${
            step.status === 'done' ? 'text-accent' :
            step.status === 'active' ? 'text-text bg-bg2' : 'text-text3'
          }`}>
            {step.status === 'done' && <span>✓</span>}
            {step.label}
          </div>
          {i < steps.length - 1 && <span className="text-border2 text-[12px] mx-1">›</span>}
        </div>
      ))}
    </div>
  );
}
```

**Step 5: 导出 index**

```ts
// frontend/src/components/ui/index.ts
export { StatusPill } from './StatusPill';
export { StatCard } from './StatCard';
export { SidebarItem, SidebarSection } from './SidebarNav';
export { ProgressBar } from './ProgressBar';
export { ProgressSteps } from './ProgressSteps';
```

**Step 6: Lint 检查**

```bash
cd frontend && bunx biome check --write src/components/ui/
```

**Step 7: Commit**

```bash
git add frontend/src/components/ui/
git commit -m "feat(frontend): add base UI component library"
```

---

## Task 3: 流式输出组件与 SSE Hook

**Files:**
- Create: `frontend/src/components/ui/ThinkingStream.tsx`
- Create: `frontend/src/components/ui/ChatBubble.tsx`
- Create: `frontend/src/hooks/useSSEStream.ts`
- Create: `frontend/src/stores/stream-store.ts`

**Step 1: Zustand 流式状态 store**

```ts
// frontend/src/stores/stream-store.ts
import { create } from 'zustand';

interface StreamState {
  thinkingText: string;
  contentText: string;
  isStreaming: boolean;
  isThinkingDone: boolean;
  reset: () => void;
  appendThinking: (delta: string) => void;
  appendContent: (delta: string) => void;
  setDone: () => void;
}

export const useStreamStore = create<StreamState>((set) => ({
  thinkingText: '',
  contentText: '',
  isStreaming: false,
  isThinkingDone: false,
  reset: () => set({ thinkingText: '', contentText: '', isStreaming: false, isThinkingDone: false }),
  appendThinking: (delta) => set((s) => ({ thinkingText: s.thinkingText + delta, isStreaming: true })),
  appendContent: (delta) => set((s) => ({ contentText: s.contentText + delta, isThinkingDone: true })),
  setDone: () => set({ isStreaming: false }),
}));
```

**Step 2: useSSEStream hook**

```ts
// frontend/src/hooks/useSSEStream.ts
import { useStreamStore } from '@/stores/stream-store';

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api';

export function useSSEStream() {
  const { reset, appendThinking, appendContent, setDone } = useStreamStore();

  async function startStream(path: string, body: object) {
    reset();
    const response = await fetch(`${API_BASE}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    if (!response.body) return;
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() ?? '';

      for (const line of lines) {
        if (line.startsWith('event: ')) {
          // 下一行是 data
        } else if (line.startsWith('data: ')) {
          // 需要知道当前 event 类型
        }
      }
    }
    setDone();
  }

  // 更健壮的解析：将 event+data 配对
  async function streamSSE(path: string, body: object) {
    reset();
    const response = await fetch(`${API_BASE}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    if (!response.body) return;
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) { setDone(); break; }
      buffer += decoder.decode(value, { stream: true });

      // 按双换行分割 SSE 消息块
      const messages = buffer.split('\n\n');
      buffer = messages.pop() ?? '';

      for (const msg of messages) {
        const eventMatch = msg.match(/^event: (\w+)/m);
        const dataMatch = msg.match(/^data: (.+)/m);
        if (!eventMatch || !dataMatch) continue;

        const eventType = eventMatch[1];
        try {
          const payload = JSON.parse(dataMatch[1]);
          if (eventType === 'thinking') appendThinking(payload.delta ?? '');
          else if (eventType === 'content') appendContent(payload.delta ?? '');
          else if (eventType === 'done') setDone();
        } catch { /* ignore parse errors */ }
      }
    }
  }

  return { streamSSE };
}
```

**Step 3: ThinkingStream 组件**

```tsx
// frontend/src/components/ui/ThinkingStream.tsx
'use client';
import { useState } from 'react';

interface ThinkingStreamProps {
  text: string;
  isStreaming: boolean;
}

export function ThinkingStream({ text, isStreaming }: ThinkingStreamProps) {
  const [collapsed, setCollapsed] = useState(false);
  if (!text && !isStreaming) return null;

  return (
    <div className="mb-3 rounded-lg border border-border overflow-hidden">
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="w-full flex items-center gap-2 px-3 py-2 bg-bg2 text-[11.5px] text-text3 hover:text-text2 transition-colors"
      >
        <span>🧠</span>
        <span>思考过程</span>
        {isStreaming && <span className="w-1.5 h-1.5 rounded-full bg-accent animate-pulse ml-1" />}
        <span className="ml-auto">{collapsed ? '▼' : '▲'}</span>
      </button>
      {!collapsed && (
        <div className="px-3 py-2 bg-bg text-text3 text-[12px] font-mono leading-relaxed whitespace-pre-wrap max-h-48 overflow-y-auto">
          {text}
          {isStreaming && <span className="inline-block w-[2px] h-[13px] bg-text3 ml-0.5 animate-[blink_1s_infinite]" />}
        </div>
      )}
    </div>
  );
}
```

**Step 4: ChatBubble 组件**

```tsx
// frontend/src/components/ui/ChatBubble.tsx
interface ChatBubbleProps {
  role: 'ai' | 'user';
  content: string;
  time?: string;
  isStreaming?: boolean;
}

export function ChatBubble({ role, content, time, isStreaming }: ChatBubbleProps) {
  const isAI = role === 'ai';
  return (
    <div className={`flex gap-2.5 mb-3.5 ${isAI ? '' : 'flex-row-reverse'}`}>
      <div className={`w-7 h-7 rounded-full flex-shrink-0 flex items-center justify-center text-[12px] font-bold ${
        isAI
          ? 'bg-[linear-gradient(135deg,rgba(0,217,163,0.1),rgba(59,130,246,0.15))] border border-[rgba(0,217,163,0.3)] text-accent'
          : 'bg-bg3 border border-border text-text2'
      }`}>
        {isAI ? 'AI' : 'U'}
      </div>
      <div>
        <div className={`rounded-lg px-3 py-2.5 max-w-[480px] text-[12.5px] leading-relaxed ${
          isAI
            ? 'bg-[rgba(0,217,163,0.04)] border border-[rgba(0,217,163,0.2)] text-text'
            : 'bg-bg2 border border-border text-text'
        }`}>
          {content}
          {isStreaming && <span className="inline-block w-[2px] h-3 bg-accent ml-0.5 animate-[blink_1s_infinite]" />}
        </div>
        {time && <div className="text-[10px] text-text3 mt-1 font-mono">{time}</div>}
      </div>
    </div>
  );
}
```

**Step 5: 更新 ui/index.ts**

```ts
export { ThinkingStream } from './ThinkingStream';
export { ChatBubble } from './ChatBubble';
```

**Step 6: Lint + Commit**

```bash
cd frontend && bunx biome check --write src/components/ui/ src/hooks/ src/stores/
git add frontend/src/
git commit -m "feat(frontend): add SSE streaming hook and ThinkingStream/ChatBubble components"
```

---

## Task 4: 后端 M06 testcases — 数据模型与迁移

**Files:**
- Create: `backend/app/modules/testcases/models.py`
- Modify: `backend/alembic/versions/` (生成新迁移)

**Step 1: 编写 models.py**

```python
# backend/app/modules/testcases/models.py
import uuid

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base_model import BaseModel


class TestCase(BaseModel):
    __tablename__ = "test_cases"

    requirement_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("requirements.id"), index=True)
    test_point_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    case_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    title: Mapped[str] = mapped_column(Text)
    priority: Mapped[str] = mapped_column(String(10), default="P1")  # P0/P1/P2
    case_type: Mapped[str] = mapped_column(String(20), default="normal")  # normal/exception/boundary/concurrent
    status: Mapped[str] = mapped_column(String(20), default="draft")  # draft/reviewed/pending_review
    source: Mapped[str] = mapped_column(String(20), default="ai")  # ai/manual
    ai_score: Mapped[float | None] = mapped_column(nullable=True)
    precondition: Mapped[str | None] = mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer, default=1)


class TestCaseStep(BaseModel):
    __tablename__ = "test_case_steps"

    test_case_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("test_cases.id"), index=True)
    step_num: Mapped[int] = mapped_column(Integer)
    action: Mapped[str] = mapped_column(Text)
    expected_result: Mapped[str] = mapped_column(Text)


class TestCaseVersion(BaseModel):
    __tablename__ = "test_case_versions"

    test_case_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("test_cases.id"), index=True)
    version: Mapped[int] = mapped_column(Integer)
    snapshot: Mapped[dict] = mapped_column(JSONB)
    change_reason: Mapped[str | None] = mapped_column(Text)
```

**Step 2: 确保 models 被 Alembic 发现（在 `__init__.py` 导出）**

```python
# backend/app/modules/testcases/__init__.py
from app.modules.testcases.models import TestCase, TestCaseStep, TestCaseVersion

__all__ = ["TestCase", "TestCaseStep", "TestCaseVersion"]
```

**Step 3: 检查 alembic/env.py 是否导入了所有模块**

打开 `backend/alembic/env.py`，确认 `target_metadata` 部分导入了新模块：

```python
# 在现有 import 块中添加
from app.modules.testcases import models as _testcases_models  # noqa: F401
```

**Step 4: 生成迁移文件**

```bash
cd backend && uv run alembic revision --autogenerate -m "add testcases tables"
# 检查生成的文件，确认包含 test_cases / test_case_steps / test_case_versions 三张表
```

**Step 5: 执行迁移**

```bash
uv run alembic upgrade head
```

**Step 6: Commit**

```bash
git add backend/app/modules/testcases/models.py backend/app/modules/testcases/__init__.py backend/alembic/
git commit -m "feat(testcases): add ORM models and db migration"
```

---

## Task 5: 后端 M06 testcases — Schemas、Service、Router

**Files:**
- Create: `backend/app/modules/testcases/schemas.py`
- Create: `backend/app/modules/testcases/service.py`
- Modify: `backend/app/modules/testcases/router.py`

**Step 1: schemas.py**

```python
# backend/app/modules/testcases/schemas.py
import uuid
from typing import Literal

from app.shared.base_schema import BaseResponse, BaseSchema


class TestCaseStepSchema(BaseSchema):
    step_num: int
    action: str
    expected_result: str


class TestCaseStepResponse(BaseResponse):
    test_case_id: uuid.UUID
    step_num: int
    action: str
    expected_result: str


class TestCaseCreate(BaseSchema):
    requirement_id: uuid.UUID
    test_point_id: uuid.UUID | None = None
    case_id: str
    title: str
    priority: Literal["P0", "P1", "P2"] = "P1"
    case_type: Literal["normal", "exception", "boundary", "concurrent"] = "normal"
    precondition: str | None = None
    steps: list[TestCaseStepSchema] = []


class TestCaseUpdate(BaseSchema):
    title: str | None = None
    priority: Literal["P0", "P1", "P2"] | None = None
    case_type: str | None = None
    status: str | None = None
    precondition: str | None = None
    steps: list[TestCaseStepSchema] | None = None


class TestCaseResponse(BaseResponse):
    requirement_id: uuid.UUID
    test_point_id: uuid.UUID | None
    case_id: str
    title: str
    priority: str
    case_type: str
    status: str
    source: str
    ai_score: float | None
    precondition: str | None
    version: int


class TestCaseListQuery(BaseSchema):
    requirement_id: uuid.UUID | None = None
    priority: str | None = None
    case_type: str | None = None
    status: str | None = None
    page: int = 1
    page_size: int = 20
```

**Step 2: service.py**

```python
# backend/app/modules/testcases/service.py
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.testcases.models import TestCase, TestCaseStep, TestCaseVersion
from app.modules.testcases.schemas import TestCaseCreate, TestCaseUpdate


class TestCaseService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, data: TestCaseCreate) -> TestCase:
        case_data = data.model_dump(exclude={"steps"})
        tc = TestCase(**case_data, source="manual")
        self.session.add(tc)
        await self.session.flush()  # 获取 tc.id

        for i, step in enumerate(data.steps, 1):
            s = TestCaseStep(test_case_id=tc.id, step_num=i, **step.model_dump())
            self.session.add(s)

        await self.session.commit()
        await self.session.refresh(tc)
        return tc

    async def list_cases(
        self,
        requirement_id: UUID | None = None,
        priority: str | None = None,
        case_type: str | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> list[TestCase]:
        q = select(TestCase).where(TestCase.deleted_at.is_(None))
        if requirement_id:
            q = q.where(TestCase.requirement_id == requirement_id)
        if priority:
            q = q.where(TestCase.priority == priority)
        if case_type:
            q = q.where(TestCase.case_type == case_type)
        if status:
            q = q.where(TestCase.status == status)
        q = q.offset((page - 1) * page_size).limit(page_size)
        result = await self.session.execute(q)
        return list(result.scalars().all())

    async def get(self, case_id: UUID) -> TestCase | None:
        return await self.session.get(TestCase, case_id)

    async def update(self, tc: TestCase, data: TestCaseUpdate) -> TestCase:
        # 快照当前版本
        snapshot = {
            "title": tc.title, "priority": tc.priority,
            "case_type": tc.case_type, "status": tc.status,
        }
        version = TestCaseVersion(
            test_case_id=tc.id,
            version=tc.version,
            snapshot=snapshot,
            change_reason="manual_edit",
        )
        self.session.add(version)

        for field, value in data.model_dump(exclude_none=True, exclude={"steps"}).items():
            setattr(tc, field, value)
        tc.version += 1

        if data.steps is not None:
            # 删旧步骤（软删除替代：直接覆盖）
            existing = await self.session.execute(
                select(TestCaseStep).where(TestCaseStep.test_case_id == tc.id)
            )
            for s in existing.scalars():
                await self.session.delete(s)
            for i, step in enumerate(data.steps, 1):
                self.session.add(TestCaseStep(test_case_id=tc.id, step_num=i, **step.model_dump()))

        await self.session.commit()
        await self.session.refresh(tc)
        return tc

    async def soft_delete(self, tc: TestCase) -> None:
        from datetime import datetime, timezone
        tc.deleted_at = datetime.now(timezone.utc)
        await self.session.commit()
```

**Step 3: router.py**

```python
# backend/app/modules/testcases/router.py
import uuid

from fastapi import APIRouter, HTTPException, status

from app.core.dependencies import AsyncSessionDep
from app.modules.testcases.schemas import (
    TestCaseCreate,
    TestCaseResponse,
    TestCaseUpdate,
)
from app.modules.testcases.service import TestCaseService

router = APIRouter(prefix="/testcases", tags=["testcases"])


@router.get("", response_model=list[TestCaseResponse])
async def list_testcases(
    session: AsyncSessionDep,
    requirement_id: uuid.UUID | None = None,
    priority: str | None = None,
    case_type: str | None = None,
    status_filter: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> list[TestCaseResponse]:
    svc = TestCaseService(session)
    cases = await svc.list_cases(requirement_id, priority, case_type, status_filter, page, page_size)
    return [TestCaseResponse.model_validate(c) for c in cases]


@router.post("", response_model=TestCaseResponse, status_code=status.HTTP_201_CREATED)
async def create_testcase(data: TestCaseCreate, session: AsyncSessionDep) -> TestCaseResponse:
    svc = TestCaseService(session)
    tc = await svc.create(data)
    return TestCaseResponse.model_validate(tc)


@router.get("/{case_id}", response_model=TestCaseResponse)
async def get_testcase(case_id: uuid.UUID, session: AsyncSessionDep) -> TestCaseResponse:
    svc = TestCaseService(session)
    tc = await svc.get(case_id)
    if not tc:
        raise HTTPException(status_code=404, detail="TestCase not found")
    return TestCaseResponse.model_validate(tc)


@router.patch("/{case_id}", response_model=TestCaseResponse)
async def update_testcase(case_id: uuid.UUID, data: TestCaseUpdate, session: AsyncSessionDep) -> TestCaseResponse:
    svc = TestCaseService(session)
    tc = await svc.get(case_id)
    if not tc:
        raise HTTPException(status_code=404, detail="TestCase not found")
    tc = await svc.update(tc, data)
    return TestCaseResponse.model_validate(tc)


@router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_testcase(case_id: uuid.UUID, session: AsyncSessionDep) -> None:
    svc = TestCaseService(session)
    tc = await svc.get(case_id)
    if not tc:
        raise HTTPException(status_code=404, detail="TestCase not found")
    await svc.soft_delete(tc)
```

**Step 4: Lint 检查**

```bash
cd backend && uv run ruff check app/modules/testcases/ && uv run ruff format app/modules/testcases/
```

**Step 5: 启动服务验证 API**

```bash
uv run uvicorn app.main:app --reload --port 8000
# 访问 http://localhost:8000/docs，确认 /api/testcases 端点存在
```

**Step 6: Commit**

```bash
git add backend/app/modules/testcases/
git commit -m "feat(testcases): implement M06 CRUD API"
```

---

## Task 6: 后端 SSE 基础设施 — ThinkingStreamAdapter

**Files:**
- Create: `backend/app/ai/__init__.py`
- Create: `backend/app/ai/stream_adapter.py`
- Create: `backend/app/ai/prompts.py`

**Step 1: 创建 AI 包**

```python
# backend/app/ai/__init__.py
```

**Step 2: ThinkingStreamAdapter**

```python
# backend/app/ai/stream_adapter.py
"""统一的流式输出适配器，支持 OpenAI / Anthropic / DeepSeek。

SSE 事件格式：
  event: thinking\ndata: {"delta": "..."}\n\n
  event: content\ndata:  {"delta": "..."}\n\n
  event: done\ndata: {"usage": {...}}\n\n
"""
import json
from collections.abc import AsyncIterator

from app.core.config import settings


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


async def openai_thinking_stream(
    messages: list[dict],
    system: str = "",
) -> AsyncIterator[str]:
    """OpenAI 流式输出：先 yield 思考步骤（模拟），再 yield 内容。"""
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=settings.openai_api_key)

    # 模拟思考过程（发送一条 thinking 事件）
    yield _sse("thinking", {"delta": "正在分析需求，梳理测试场景...\n"})

    all_messages = messages
    if system:
        all_messages = [{"role": "system", "content": system}, *messages]

    stream = await client.chat.completions.create(
        model=settings.openai_model,
        messages=all_messages,
        stream=True,
    )

    async for chunk in stream:
        delta = chunk.choices[0].delta.content or ""
        if delta:
            yield _sse("content", {"delta": delta})

    yield _sse("done", {"usage": {}})


async def anthropic_thinking_stream(
    messages: list[dict],
    system: str = "",
) -> AsyncIterator[str]:
    """Claude 扩展思考流式输出。"""
    import anthropic

    client = anthropic.AsyncAnthropic()

    async with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=16000,
        thinking={"type": "enabled", "budget_tokens": 10000},
        system=system,
        messages=messages,
    ) as stream:
        async for event in stream:
            if event.type == "content_block_start":
                pass
            elif event.type == "content_block_delta":
                if event.delta.type == "thinking_delta":
                    yield _sse("thinking", {"delta": event.delta.thinking})
                elif event.delta.type == "text_delta":
                    yield _sse("content", {"delta": event.delta.text})

    yield _sse("done", {"usage": {}})


async def get_thinking_stream(
    messages: list[dict],
    system: str = "",
) -> AsyncIterator[str]:
    """根据 settings.llm_provider 选择适配器。"""
    provider = settings.llm_provider.lower()
    if provider == "anthropic":
        return anthropic_thinking_stream(messages, system)
    # 默认 openai
    return openai_thinking_stream(messages, system)
```

**Step 3: 提示词模板**

```python
# backend/app/ai/prompts.py

DIAGNOSIS_SYSTEM = """你是一个资深测试专家，专注于数据中台场景的测试设计。
你的任务是分析需求文档，找出可能遗漏的测试场景，包括：
- 异常流程和边界条件
- 并发和性能场景
- 权限和安全场景
- 数据一致性场景
- 行业最佳实践中的必测项

请先在思考过程中系统分析，再给出结构化的诊断结果。"""

SCENE_MAP_SYSTEM = """你是一个资深测试设计专家。
根据需求文档和诊断报告，生成完整的测试点列表。
每个测试点需要包含：分组、标题、描述、优先级、预计用例数。
按照正常流程、异常场景、边界值、权限安全分组。"""

GENERATION_SYSTEM = """你是一个专业的测试用例编写专家，专注于数据中台场景。
根据提供的测试点，生成详细的测试用例，包含：
- 用例标题（简明扼要）
- 优先级（P0/P1/P2）
- 前置条件
- 详细步骤（操作 + 预期结果）
- 用例类型（正常/异常/边界/并发）

生成的用例应覆盖测试点的所有场景，步骤清晰可执行。"""
```

**Step 4: Lint + Commit**

```bash
cd backend && uv run ruff check app/ai/ && uv run ruff format app/ai/
git add backend/app/ai/
git commit -m "feat(ai): add ThinkingStreamAdapter and prompt templates"
```

---

## Task 7: 后端 M04 scene_map — 数据模型与 API

**Files:**
- Create: `backend/app/modules/scene_map/models.py`
- Create: `backend/app/modules/scene_map/schemas.py`
- Create: `backend/app/modules/scene_map/service.py`
- Modify: `backend/app/modules/scene_map/router.py`

**Step 1: models.py**

```python
# backend/app/modules/scene_map/models.py
import uuid
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.shared.base_model import BaseModel


class SceneMap(BaseModel):
    __tablename__ = "scene_maps"
    requirement_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("requirements.id"), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(20), default="draft")  # draft/confirmed
    confirmed_at: Mapped[str | None] = mapped_column(nullable=True)


class TestPoint(BaseModel):
    __tablename__ = "test_points"
    scene_map_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("scene_maps.id"), index=True)
    group_name: Mapped[str] = mapped_column(String(50))  # 正常流程/异常场景/边界值/权限安全
    title: Mapped[str] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    priority: Mapped[str] = mapped_column(String(10), default="P1")
    status: Mapped[str] = mapped_column(String(20), default="ai_generated")
    # ai_generated / confirmed / manual / pending
    estimated_cases: Mapped[int] = mapped_column(Integer, default=3)
    source: Mapped[str] = mapped_column(String(20), default="ai")  # ai/manual
```

**Step 2: schemas.py**

```python
# backend/app/modules/scene_map/schemas.py
import uuid
from app.shared.base_schema import BaseResponse, BaseSchema


class TestPointCreate(BaseSchema):
    group_name: str
    title: str
    description: str | None = None
    priority: str = "P1"
    estimated_cases: int = 3


class TestPointUpdate(BaseSchema):
    title: str | None = None
    description: str | None = None
    priority: str | None = None
    status: str | None = None
    estimated_cases: int | None = None


class TestPointResponse(BaseResponse):
    scene_map_id: uuid.UUID
    group_name: str
    title: str
    description: str | None
    priority: str
    status: str
    estimated_cases: int
    source: str


class SceneMapResponse(BaseResponse):
    requirement_id: uuid.UUID
    status: str
    test_points: list[TestPointResponse] = []


class GenerateRequest(BaseSchema):
    """AI 生成测试点请求体。"""
    context: str | None = None  # 额外上下文提示
```

**Step 3: service.py**

```python
# backend/app/modules/scene_map/service.py
import uuid
from collections.abc import AsyncIterator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.prompts import SCENE_MAP_SYSTEM
from app.ai.stream_adapter import get_thinking_stream
from app.modules.products.models import Requirement
from app.modules.scene_map.models import SceneMap, TestPoint
from app.modules.scene_map.schemas import TestPointCreate, TestPointUpdate


class SceneMapService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_or_create(self, requirement_id: uuid.UUID) -> SceneMap:
        result = await self.session.execute(
            select(SceneMap).where(
                SceneMap.requirement_id == requirement_id,
                SceneMap.deleted_at.is_(None),
            )
        )
        sm = result.scalar_one_or_none()
        if not sm:
            sm = SceneMap(requirement_id=requirement_id)
            self.session.add(sm)
            await self.session.commit()
            await self.session.refresh(sm)
        return sm

    async def list_test_points(self, scene_map_id: uuid.UUID) -> list[TestPoint]:
        result = await self.session.execute(
            select(TestPoint).where(
                TestPoint.scene_map_id == scene_map_id,
                TestPoint.deleted_at.is_(None),
            )
        )
        return list(result.scalars().all())

    async def add_test_point(self, scene_map_id: uuid.UUID, data: TestPointCreate) -> TestPoint:
        tp = TestPoint(scene_map_id=scene_map_id, source="manual", **data.model_dump())
        self.session.add(tp)
        await self.session.commit()
        await self.session.refresh(tp)
        return tp

    async def update_test_point(self, tp: TestPoint, data: TestPointUpdate) -> TestPoint:
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(tp, field, value)
        await self.session.commit()
        await self.session.refresh(tp)
        return tp

    async def soft_delete_test_point(self, tp: TestPoint) -> None:
        from datetime import datetime, timezone
        tp.deleted_at = datetime.now(timezone.utc)
        await self.session.commit()

    async def generate_stream(self, requirement_id: uuid.UUID) -> AsyncIterator[str]:
        """调用 AI 生成测试点，返回 SSE 流。"""
        req = await self.session.get(Requirement, requirement_id)
        if not req:
            async def _err() -> AsyncIterator[str]:
                yield "event: done\ndata: {}\n\n"
            return _err()

        content = req.content_ast.get("content", str(req.title))
        messages = [{"role": "user", "content": f"需求标题：{req.title}\n\n需求内容：{content}\n\n请生成测试点列表。"}]
        return await get_thinking_stream(messages, SCENE_MAP_SYSTEM)
```

**Step 4: router.py**

```python
# backend/app/modules/scene_map/router.py
import uuid

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.core.dependencies import AsyncSessionDep
from app.modules.scene_map.schemas import (
    GenerateRequest,
    SceneMapResponse,
    TestPointCreate,
    TestPointResponse,
    TestPointUpdate,
)
from app.modules.scene_map.service import SceneMapService

router = APIRouter(prefix="/scene-map", tags=["scene-map"])


@router.get("/{requirement_id}", response_model=SceneMapResponse)
async def get_scene_map(requirement_id: uuid.UUID, session: AsyncSessionDep) -> SceneMapResponse:
    svc = SceneMapService(session)
    sm = await svc.get_or_create(requirement_id)
    tps = await svc.list_test_points(sm.id)
    resp = SceneMapResponse.model_validate(sm)
    resp.test_points = [TestPointResponse.model_validate(tp) for tp in tps]
    return resp


@router.post("/{requirement_id}/generate")
async def generate_test_points(
    requirement_id: uuid.UUID, _body: GenerateRequest, session: AsyncSessionDep
) -> StreamingResponse:
    svc = SceneMapService(session)
    stream = await svc.generate_stream(requirement_id)
    return StreamingResponse(stream, media_type="text/event-stream")


@router.post("/{requirement_id}/test-points", response_model=TestPointResponse)
async def add_test_point(requirement_id: uuid.UUID, data: TestPointCreate, session: AsyncSessionDep) -> TestPointResponse:
    svc = SceneMapService(session)
    sm = await svc.get_or_create(requirement_id)
    tp = await svc.add_test_point(sm.id, data)
    return TestPointResponse.model_validate(tp)


@router.patch("/test-points/{tp_id}", response_model=TestPointResponse)
async def update_test_point(tp_id: uuid.UUID, data: TestPointUpdate, session: AsyncSessionDep) -> TestPointResponse:
    from sqlalchemy import select
    from app.modules.scene_map.models import TestPoint
    result = await session.execute(select(TestPoint).where(TestPoint.id == tp_id))
    tp = result.scalar_one_or_none()
    if not tp:
        raise HTTPException(status_code=404, detail="TestPoint not found")
    svc = SceneMapService(session)
    tp = await svc.update_test_point(tp, data)
    return TestPointResponse.model_validate(tp)


@router.delete("/test-points/{tp_id}", status_code=204)
async def delete_test_point(tp_id: uuid.UUID, session: AsyncSessionDep) -> None:
    from sqlalchemy import select
    from app.modules.scene_map.models import TestPoint
    result = await session.execute(select(TestPoint).where(TestPoint.id == tp_id))
    tp = result.scalar_one_or_none()
    if not tp:
        raise HTTPException(status_code=404, detail="TestPoint not found")
    svc = SceneMapService(session)
    await svc.soft_delete_test_point(tp)
```

**Step 5: 生成迁移并执行**

```bash
cd backend
# 确保 alembic/env.py 导入了新模块
# 添加: from app.modules.scene_map import models as _scene_map_models  # noqa: F401
uv run alembic revision --autogenerate -m "add scene_map and test_points tables"
uv run alembic upgrade head
```

**Step 6: Lint + Commit**

```bash
uv run ruff check app/modules/scene_map/ && uv run ruff format app/modules/scene_map/
git add backend/app/modules/scene_map/ backend/alembic/
git commit -m "feat(scene-map): implement M04 scene map and test points API with SSE generation"
```

---

## Task 8: 后端 M03 diagnosis — 诊断模块

**Files:**
- Create: `backend/app/modules/diagnosis/models.py`
- Create: `backend/app/modules/diagnosis/schemas.py`
- Create: `backend/app/modules/diagnosis/service.py`
- Modify: `backend/app/modules/diagnosis/router.py`

**Step 1: models.py**

```python
# backend/app/modules/diagnosis/models.py
import uuid
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.shared.base_model import BaseModel


class DiagnosisReport(BaseModel):
    __tablename__ = "diagnosis_reports"
    requirement_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("requirements.id"), index=True)
    status: Mapped[str] = mapped_column(String(20), default="running")  # running/done/failed
    overall_score: Mapped[float | None] = mapped_column(nullable=True)
    summary: Mapped[str | None] = mapped_column(Text)
    risk_count_high: Mapped[int] = mapped_column(Integer, default=0)
    risk_count_medium: Mapped[int] = mapped_column(Integer, default=0)
    risk_count_industry: Mapped[int] = mapped_column(Integer, default=0)


class DiagnosisRisk(BaseModel):
    __tablename__ = "diagnosis_risks"
    report_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("diagnosis_reports.id"), index=True)
    level: Mapped[str] = mapped_column(String(20))  # high/medium/industry
    title: Mapped[str] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    risk_status: Mapped[str] = mapped_column(String(20), default="pending")  # pending/acknowledged/resolved


class DiagnosisChatMessage(BaseModel):
    __tablename__ = "diagnosis_chat_messages"
    report_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("diagnosis_reports.id"), index=True)
    role: Mapped[str] = mapped_column(String(10))  # user/assistant
    content: Mapped[str] = mapped_column(Text)
    round_num: Mapped[int] = mapped_column(Integer, default=1)
```

**Step 2: schemas.py**

```python
# backend/app/modules/diagnosis/schemas.py
import uuid
from app.shared.base_schema import BaseResponse, BaseSchema


class DiagnosisRiskResponse(BaseResponse):
    report_id: uuid.UUID
    level: str
    title: str
    description: str | None
    risk_status: str


class DiagnosisReportResponse(BaseResponse):
    requirement_id: uuid.UUID
    status: str
    overall_score: float | None
    summary: str | None
    risk_count_high: int
    risk_count_medium: int
    risk_count_industry: int
    risks: list[DiagnosisRiskResponse] = []


class ChatRequest(BaseSchema):
    message: str
    round_num: int = 1


class RiskStatusUpdate(BaseSchema):
    risk_status: str  # acknowledged/resolved
```

**Step 3: service.py**

```python
# backend/app/modules/diagnosis/service.py
import uuid
from collections.abc import AsyncIterator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.prompts import DIAGNOSIS_SYSTEM
from app.ai.stream_adapter import get_thinking_stream
from app.modules.diagnosis.models import DiagnosisChatMessage, DiagnosisReport, DiagnosisRisk
from app.modules.diagnosis.schemas import ChatRequest, RiskStatusUpdate
from app.modules.products.models import Requirement


class DiagnosisService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_report(self, requirement_id: uuid.UUID) -> DiagnosisReport | None:
        result = await self.session.execute(
            select(DiagnosisReport).where(
                DiagnosisReport.requirement_id == requirement_id,
                DiagnosisReport.deleted_at.is_(None),
            ).order_by(DiagnosisReport.created_at.desc())
        )
        return result.scalar_one_or_none()

    async def list_risks(self, report_id: uuid.UUID) -> list[DiagnosisRisk]:
        result = await self.session.execute(
            select(DiagnosisRisk).where(
                DiagnosisRisk.report_id == report_id,
                DiagnosisRisk.deleted_at.is_(None),
            )
        )
        return list(result.scalars().all())

    async def run_stream(self, requirement_id: uuid.UUID) -> AsyncIterator[str]:
        req = await self.session.get(Requirement, requirement_id)
        if not req:
            async def _err() -> AsyncIterator[str]:
                yield "event: done\ndata: {}\n\n"
            return _err()

        # 创建报告记录
        report = DiagnosisReport(requirement_id=requirement_id, status="running")
        self.session.add(report)
        await self.session.commit()

        content = req.content_ast.get("content", req.title)
        messages = [{"role": "user", "content": f"需求标题：{req.title}\n\n需求内容：{content}\n\n请分析该需求的测试遗漏风险。"}]
        return await get_thinking_stream(messages, DIAGNOSIS_SYSTEM)

    async def chat_stream(self, requirement_id: uuid.UUID, data: ChatRequest) -> AsyncIterator[str]:
        report = await self.get_report(requirement_id)
        if not report:
            async def _err() -> AsyncIterator[str]:
                yield "event: done\ndata: {}\n\n"
            return _err()

        # 保存用户消息
        user_msg = DiagnosisChatMessage(
            report_id=report.id, role="user",
            content=data.message, round_num=data.round_num,
        )
        self.session.add(user_msg)
        await self.session.commit()

        # 获取历史消息
        hist_result = await self.session.execute(
            select(DiagnosisChatMessage)
            .where(DiagnosisChatMessage.report_id == report.id)
            .order_by(DiagnosisChatMessage.created_at)
        )
        history = [{"role": m.role, "content": m.content} for m in hist_result.scalars()]
        return await get_thinking_stream(history, DIAGNOSIS_SYSTEM)

    async def update_risk_status(self, risk_id: uuid.UUID, data: RiskStatusUpdate) -> DiagnosisRisk | None:
        risk = await self.session.get(DiagnosisRisk, risk_id)
        if not risk:
            return None
        risk.risk_status = data.risk_status
        await self.session.commit()
        await self.session.refresh(risk)
        return risk
```

**Step 4: router.py**

```python
# backend/app/modules/diagnosis/router.py
import uuid

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.core.dependencies import AsyncSessionDep
from app.modules.diagnosis.schemas import (
    ChatRequest,
    DiagnosisReportResponse,
    DiagnosisRiskResponse,
    RiskStatusUpdate,
)
from app.modules.diagnosis.service import DiagnosisService

router = APIRouter(prefix="/diagnosis", tags=["diagnosis"])


@router.get("/{requirement_id}", response_model=DiagnosisReportResponse)
async def get_diagnosis(requirement_id: uuid.UUID, session: AsyncSessionDep) -> DiagnosisReportResponse:
    svc = DiagnosisService(session)
    report = await svc.get_report(requirement_id)
    if not report:
        raise HTTPException(status_code=404, detail="Diagnosis report not found")
    risks = await svc.list_risks(report.id)
    resp = DiagnosisReportResponse.model_validate(report)
    resp.risks = [DiagnosisRiskResponse.model_validate(r) for r in risks]
    return resp


@router.post("/{requirement_id}/run")
async def run_diagnosis(requirement_id: uuid.UUID, session: AsyncSessionDep) -> StreamingResponse:
    svc = DiagnosisService(session)
    stream = await svc.run_stream(requirement_id)
    return StreamingResponse(stream, media_type="text/event-stream")


@router.post("/{requirement_id}/chat")
async def diagnosis_chat(requirement_id: uuid.UUID, data: ChatRequest, session: AsyncSessionDep) -> StreamingResponse:
    svc = DiagnosisService(session)
    stream = await svc.chat_stream(requirement_id, data)
    return StreamingResponse(stream, media_type="text/event-stream")


@router.patch("/{requirement_id}/risks/{risk_id}", response_model=DiagnosisRiskResponse)
async def update_risk(requirement_id: uuid.UUID, risk_id: uuid.UUID, data: RiskStatusUpdate, session: AsyncSessionDep) -> DiagnosisRiskResponse:
    svc = DiagnosisService(session)
    risk = await svc.update_risk_status(risk_id, data)
    if not risk:
        raise HTTPException(status_code=404, detail="Risk not found")
    return DiagnosisRiskResponse.model_validate(risk)
```

**Step 5: 生成迁移并执行**

```bash
cd backend
# alembic/env.py 添加: from app.modules.diagnosis import models as _diag_models  # noqa: F401
uv run alembic revision --autogenerate -m "add diagnosis tables"
uv run alembic upgrade head
uv run ruff check app/modules/diagnosis/ && uv run ruff format app/modules/diagnosis/
```

**Step 6: Commit**

```bash
git add backend/app/modules/diagnosis/ backend/alembic/
git commit -m "feat(diagnosis): implement M03 diagnosis API with SSE streaming"
```

---

## Task 9: 后端 M05 generation — 用例生成会话

**Files:**
- Create: `backend/app/modules/generation/models.py`
- Create: `backend/app/modules/generation/schemas.py`
- Create: `backend/app/modules/generation/service.py`
- Modify: `backend/app/modules/generation/router.py`

**Step 1: models.py**

```python
# backend/app/modules/generation/models.py
import uuid
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from app.shared.base_model import BaseModel


class GenerationSession(BaseModel):
    __tablename__ = "generation_sessions"
    requirement_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("requirements.id"), index=True)
    mode: Mapped[str] = mapped_column(String(30), default="test_point_driven")
    # test_point_driven / document / dialogue / template
    status: Mapped[str] = mapped_column(String(20), default="active")
    model_used: Mapped[str] = mapped_column(String(50), default="gpt-4o")


class GenerationMessage(BaseModel):
    __tablename__ = "generation_messages"
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("generation_sessions.id"), index=True)
    role: Mapped[str] = mapped_column(String(10))  # user/assistant
    content: Mapped[str] = mapped_column(Text)
    thinking_content: Mapped[str | None] = mapped_column(Text)
    token_count: Mapped[int] = mapped_column(Integer, default=0)
```

**Step 2: schemas.py + service.py + router.py**

参照 Task 8 的 diagnosis 模式实现，关键差异：
- `POST /api/generation/sessions` 创建会话，返回 `session_id`
- `POST /api/generation/sessions/{session_id}/chat` 返回 SSE 流，消息包含生成的用例 JSON
- `GET  /api/generation/sessions/{session_id}/cases` 查询已接受的用例（从 testcases 表）
- `POST /api/generation/sessions/{session_id}/cases/{case_id}/accept` 将草稿用例写入 testcases 表

生成系统提示使用 `GENERATION_SYSTEM`（来自 `app.ai.prompts`）。

**Step 3: 生成迁移并执行**

```bash
# alembic/env.py 添加: from app.modules.generation import models as _gen_models  # noqa: F401
uv run alembic revision --autogenerate -m "add generation_sessions and messages tables"
uv run alembic upgrade head
uv run ruff check app/modules/generation/ && uv run ruff format app/modules/generation/
git add backend/app/modules/generation/ backend/alembic/
git commit -m "feat(generation): implement M05 generation session API"
```

---

## Task 10: 更新 (main) layout — 侧边栏导航

**Files:**
- Modify: `frontend/src/app/(main)/layout.tsx`

**Step 1: 实现带导航的主布局**

```tsx
// frontend/src/app/(main)/layout.tsx
'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { SidebarItem, SidebarSection } from '@/components/ui';

const navItems = [
  { href: '/', icon: '🏠', label: '项目总览' },
  { section: '测试流程' },
  { href: '/requirements', icon: '📄', label: '需求管理' },
  { href: '/diagnosis', icon: '🩺', label: '健康诊断' },
  { href: '/scene-map', icon: '🌳', label: '测试点确认' },
  { href: '/workbench', icon: '⚡', label: '生成工作台' },
  { href: '/testcases', icon: '📋', label: '用例管理' },
  { section: '分析' },
  { href: '/analytics', icon: '📊', label: '质量看板' },
  { href: '/knowledge', icon: '🧠', label: '知识库' },
];

export default function MainLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <aside className="w-[220px] bg-bg1 border-r border-border min-h-screen fixed top-0 left-0 flex flex-col">
        <div className="p-4 border-b border-border">
          <div className="font-display font-bold text-[15px] text-accent tracking-wide">TestGen Pro</div>
        </div>
        <nav className="flex-1 py-4 overflow-y-auto">
          {navItems.map((item, i) =>
            'section' in item ? (
              <SidebarSection key={i} label={item.section}>{null}</SidebarSection>
            ) : (
              <div key={item.href} className="px-3">
                <Link href={item.href}>
                  <SidebarItem
                    icon={item.icon}
                    label={item.label}
                    active={pathname === item.href || (item.href !== '/' && pathname.startsWith(item.href))}
                  />
                </Link>
              </div>
            )
          )}
        </nav>
      </aside>
      {/* Main content */}
      <main className="ml-[220px] flex-1 min-h-screen bg-bg">
        {children}
      </main>
    </div>
  );
}
```

**Step 2: Commit**

```bash
git add frontend/src/app/\(main\)/layout.tsx
git commit -m "feat(frontend): implement main layout with sidebar navigation"
```

---

## Task 11: 前端 P1 项目列表 `/`

**Files:**
- Modify: `frontend/src/app/(main)/page.tsx`
- Create: `frontend/src/app/(main)/_components/ProjectCard.tsx`

**Step 1: ProjectCard 组件**

```tsx
// frontend/src/app/(main)/_components/ProjectCard.tsx
import Link from 'next/link';
import { StatusPill, ProgressBar } from '@/components/ui';

interface ProjectCardProps {
  id: string;
  name: string;
  iteration: string;
  status: 'active' | 'completed' | 'paused';
  totalCases: number;
  coverage: number;
  pending: number;
  members: string[];
}

const statusMap = {
  active: { variant: 'green' as const, label: '进行中' },
  completed: { variant: 'gray' as const, label: '已完成' },
  paused: { variant: 'amber' as const, label: '暂停' },
};

export function ProjectCard({ id, name, iteration, status, totalCases, coverage, pending, members }: ProjectCardProps) {
  const s = statusMap[status];
  return (
    <Link href={`/requirements?product=${id}`}>
      <div className="bg-bg1 border border-border rounded-[10px] p-4 cursor-pointer hover:border-border2 hover:-translate-y-px transition-all">
        <div className="flex items-start justify-between mb-3">
          <div>
            <div className="font-semibold text-[13.5px] text-text">{name}</div>
            <div className="text-text3 text-[11.5px] mt-0.5">{iteration}</div>
          </div>
          <StatusPill variant={s.variant}>{s.label}</StatusPill>
        </div>
        <div className="grid grid-cols-3 gap-2 mb-3">
          {[
            { val: totalCases, label: '用例总数' },
            { val: `${coverage}%`, label: '覆盖率', color: 'text-accent' },
            { val: pending, label: '待处理', color: pending > 0 ? 'text-amber' : undefined },
          ].map((stat, i) => (
            <div key={i} className="text-center p-2 bg-bg2 rounded-md">
              <div className={`font-mono text-[18px] font-semibold ${stat.color ?? 'text-text'}`}>{stat.val}</div>
              <div className="text-[10.5px] text-text3">{stat.label}</div>
            </div>
          ))}
        </div>
        <ProgressBar value={coverage} />
        <div className="mt-2.5 text-[11.5px] text-text3">👥 {members.slice(0, 3).join('  ')}</div>
      </div>
    </Link>
  );
}
```

**Step 2: 页面本体**

```tsx
// frontend/src/app/(main)/page.tsx
'use client';
import { useQuery } from '@tanstack/react-query';
import { StatCard } from '@/components/ui';
import { ProjectCard } from './_components/ProjectCard';
import { apiClient } from '@/lib/api-client';

export default function ProjectListPage() {
  const { data: products = [] } = useQuery({
    queryKey: ['products'],
    queryFn: () => apiClient<{ id: string; name: string; slug: string }[]>('/products'),
  });

  return (
    <div className="p-6 max-w-[1200px] mx-auto">
      {/* Topbar */}
      <div className="flex items-center gap-3 mb-6">
        <div>
          <div className="font-mono text-[10px] text-text3 uppercase tracking-wide">TESTGEN PRO · 项目列表</div>
          <h1 className="font-display font-bold text-[20px]">全部项目</h1>
          <div className="text-text3 text-[12px]">{products.length} 个子产品</div>
        </div>
        <div className="flex-1" />
        <input className="bg-bg2 border border-border rounded-md px-3 py-1.5 text-[13px] text-text outline-none focus:border-accent w-[220px] placeholder:text-text3" placeholder="🔍  搜索项目..." />
        <button className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-md text-[12.5px] font-semibold bg-accent text-black border border-accent hover:bg-accent2 transition-colors">
          ＋ 新建项目
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-3 mb-6">
        <StatCard value="847" label="本周生成用例" delta="↑ 23% 较上周" highlighted />
        <StatCard value="12" label="进行中迭代" delta="3 个 Sprint 本周截止" deltaColor="text-amber" />
        <StatCard value="94%" label="平均用例覆盖率" progress={94} />
        <StatCard value="18" label="待处理健康诊断" delta="需要补充场景" deltaColor="text-red" />
      </div>

      {/* Project grid */}
      <div className="grid grid-cols-3 gap-4">
        {products.map((p) => (
          <ProjectCard
            key={p.id}
            id={p.id}
            name={p.name}
            iteration="当前迭代"
            status="active"
            totalCases={0}
            coverage={0}
            pending={0}
            members={[]}
          />
        ))}
        {/* 新建卡片 */}
        <div className="bg-bg1 border border-dashed border-border2 rounded-[10px] p-4 flex flex-col items-center justify-center gap-2 cursor-pointer hover:border-accent hover:text-accent transition-colors text-text3 min-h-[180px]">
          <span className="text-2xl">＋</span>
          <span className="text-[12.5px]">新建项目</span>
        </div>
      </div>
    </div>
  );
}
```

**Step 3: Lint + Commit**

```bash
cd frontend && bunx biome check --write src/app/\(main\)/
git add frontend/src/app/\(main\)/
git commit -m "feat(frontend): implement P1 project list page"
```

---

## Task 12: 前端 P6 用例管理 `/testcases`

**Files:**
- Modify: `frontend/src/app/(main)/testcases/page.tsx`

**Step 1: 页面实现**

```tsx
// frontend/src/app/(main)/testcases/page.tsx
'use client';
import { useQuery } from '@tanstack/react-query';
import { Table } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { StatusPill } from '@/components/ui';
import { apiClient } from '@/lib/api-client';

interface TestCase {
  id: string;
  case_id: string;
  title: string;
  priority: 'P0' | 'P1' | 'P2';
  case_type: string;
  status: string;
  source: string;
}

const priorityVariant = { P0: 'red', P1: 'amber', P2: 'gray' } as const;
const statusVariant = { draft: 'gray', reviewed: 'green', pending_review: 'amber' } as const;
const statusLabel = { draft: '草稿', reviewed: '已评审', pending_review: '待复核' };

export default function TestCasesPage() {
  const { data: cases = [], isLoading } = useQuery({
    queryKey: ['testcases'],
    queryFn: () => apiClient<TestCase[]>('/testcases?page_size=50'),
  });

  const columns: ColumnsType<TestCase> = [
    { title: '用例 ID', dataIndex: 'case_id', key: 'case_id', width: 120, render: (v) => <span className="font-mono text-[11px] text-text3">{v}</span> },
    { title: '标题', dataIndex: 'title', key: 'title', ellipsis: true },
    { title: '优先级', dataIndex: 'priority', key: 'priority', width: 80, render: (v) => <StatusPill variant={priorityVariant[v as keyof typeof priorityVariant] ?? 'gray'}>{v}</StatusPill> },
    { title: '类型', dataIndex: 'case_type', key: 'case_type', width: 80, render: (v) => <span className="text-text3 text-[12px]">{v}</span> },
    { title: '状态', dataIndex: 'status', key: 'status', width: 90, render: (v) => <StatusPill variant={statusVariant[v as keyof typeof statusVariant] ?? 'gray'}>{statusLabel[v as keyof typeof statusLabel] ?? v}</StatusPill> },
    { title: '来源', dataIndex: 'source', key: 'source', width: 70, render: (v) => <span className="text-text3 text-[12px]">{v === 'ai' ? '🤖 AI' : '✏️ 手动'}</span> },
    { title: '操作', key: 'action', width: 120, render: () => (
      <div className="flex gap-2">
        <button className="text-[11.5px] text-text3 hover:text-accent transition-colors">✏️ 编辑</button>
        <button className="text-[11.5px] text-text3 hover:text-text transition-colors">👁 查看</button>
      </div>
    )},
  ];

  return (
    <div className="p-6">
      <div className="flex items-center gap-3 mb-5">
        <div>
          <h1 className="font-display font-bold text-[20px]">用例管理</h1>
          <div className="text-text3 text-[12px]">{cases.length} 条用例</div>
        </div>
        <div className="flex-1" />
        <input className="bg-bg2 border border-border rounded-md px-3 py-1.5 text-[13px] text-text outline-none focus:border-accent w-[200px] placeholder:text-text3" placeholder="🔍  搜索用例..." />
        <button className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-md text-[12.5px] font-semibold bg-accent text-black border border-accent hover:bg-accent2 transition-colors">
          ＋ 手动添加
        </button>
      </div>

      {/* Filter bar */}
      <div className="flex gap-2 mb-4 flex-wrap">
        {['全部', 'P0', 'P1', 'P2'].map((f) => (
          <button key={f} className="px-3 py-1 rounded-md text-[11.5px] border border-border text-text3 hover:border-border2 hover:text-text transition-colors">{f}</button>
        ))}
        <div className="w-px bg-border mx-1" />
        {['正常', '异常', '边界', '并发'].map((f) => (
          <button key={f} className="px-3 py-1 rounded-md text-[11.5px] border border-border text-text3 hover:border-border2 hover:text-text transition-colors">{f}</button>
        ))}
      </div>

      <div className="bg-bg1 border border-border rounded-[10px] overflow-hidden">
        <Table
          dataSource={cases}
          columns={columns}
          rowKey="id"
          loading={isLoading}
          pagination={{ pageSize: 20, size: 'small' }}
          size="small"
        />
      </div>
    </div>
  );
}
```

**Step 2: Commit**

```bash
cd frontend && bunx biome check --write src/app/\(main\)/testcases/
git add frontend/src/app/\(main\)/testcases/
git commit -m "feat(frontend): implement P6 test case management page"
```

---

## Task 13: 前端 P3 健康诊断 `/diagnosis/[id]`

**Files:**
- Create: `frontend/src/app/(main)/diagnosis/[id]/page.tsx`

**Step 1: 三列诊断页面**

页面结构：`DiagnosisThreeCol`（`grid-cols-[300px_1fr_280px]`）

- **左列**：风险列表，按 `level` 分组（high/medium/industry），每项显示标题、描述、风险状态按钮
- **中列**：`ChatBubble` 历史 + `ThinkingStream` + `ChatInput`。初始加载时调用 `POST /api/diagnosis/{id}/run` 启动诊断；用户输入后调用 `POST /api/diagnosis/{id}/chat`
- **右列**：场景地图预览（调用 `GET /api/scene-map/{id}`，显示测试点统计和列表）

关键实现：
```tsx
const { streamSSE } = useSSEStream();
const { thinkingText, contentText, isStreaming } = useStreamStore();

// 启动诊断
async function runDiagnosis() {
  await streamSSE(`/diagnosis/${id}/run`, {});
}
```

**Step 2: Commit**

```bash
git add frontend/src/app/\(main\)/diagnosis/
git commit -m "feat(frontend): implement P3 health diagnosis page with SSE streaming"
```

---

## Task 14: 前端 P4 测试点确认 `/scene-map/[id]`

**Files:**
- Create: `frontend/src/app/(main)/scene-map/[id]/page.tsx`

**Step 1: 三列测试点页面**

页面结构：`SceneMapThreeCol`（`grid-cols-[260px_1fr_300px]`）

- **左列**：`TestPointList`，按 `group_name` 分组，复选框控制 `status`，点击测试点在中列显示详情
- **中列**：`TestPointDetail`，显示标题/描述/粒度/预计用例数，「AI 生成」按钮触发 `POST /api/scene-map/{id}/generate` SSE 流
- **右列**：CSS 树形可视化，用 `border-l` + `before:` 伪元素模拟树形连线；导出按钮（调用 `GET /api/scene-map/{id}/export?format=json`）

**Step 2: Commit**

```bash
git add frontend/src/app/\(main\)/scene-map/
git commit -m "feat(frontend): implement P4 scene map test point confirmation page"
```

---

## Task 15: 前端 P5 生成工作台 `/workbench/[id]`

**Files:**
- Create: `frontend/src/app/(main)/workbench/[id]/page.tsx`
- Create: `frontend/src/app/(main)/workbench/[id]/_components/CasePreviewCard.tsx`

**Step 1: 工作台三列布局（全屏，无侧边栏内容）**

页面 layout 设为 `h-screen overflow-hidden flex flex-col`：

```tsx
<div className="flex flex-col h-screen overflow-hidden">
  {/* Toolbar: 模式切换 */}
  <WorkbenchToolbar mode={mode} onModeChange={setMode} />

  {/* Three-col */}
  <div className="flex-1 grid grid-cols-[240px_1fr_340px] border border-border rounded-[10px] overflow-hidden min-h-0">
    {/* 左列：需求导航 */}
    <RequirementNav requirementId={id} />

    {/* 中列：AI 对话 */}
    <div className="flex flex-col bg-bg overflow-hidden">
      <div className="flex-1 overflow-y-auto p-4">
        {messages.map((m) => <ChatBubble key={m.id} role={m.role} content={m.content} />)}
        <ThinkingStream text={thinkingText} isStreaming={isStreaming} />
        {contentText && <ChatBubble role="ai" content={contentText} isStreaming={isStreaming} />}
      </div>
      <ChatInput onSend={handleSend} />
    </div>

    {/* 右列：用例预览列表 */}
    <CasePreviewList sessionId={sessionId} />
  </div>
</div>
```

**Step 2: CasePreviewCard**

展示生成中/已生成的用例，优先级用颜色区分，步骤数显示，「接受」按钮调用 `POST /api/generation/sessions/{session_id}/cases/{case_id}/accept`。

**Step 3: Commit**

```bash
git add frontend/src/app/\(main\)/workbench/
git commit -m "feat(frontend): implement P5 generation workbench with three-col SSE streaming"
```

---

## Task 16: 前端 P2 需求卡片 `/requirements/[id]`

**Files:**
- Create: `frontend/src/app/(main)/requirements/[id]/page.tsx`

**Step 1: 需求详情页面**

两列布局：左侧边栏（子产品/迭代/需求列表三级导航）+ 主内容区

主内容：
- `RequirementMeta`：优先级（`frontmatter.priority`）/ 状态 / 负责人
- `RichEditor`：`content_ast.content` 字段的文本展示（阶段一用 `<textarea>`，不引入复杂富文本编辑器）
- 右侧 `LinkedPanel`：关联测试点数量（调用 `GET /api/scene-map/{id}`）+ 关联用例数（调用 `GET /api/testcases?requirement_id={id}`）
- 「开始健康诊断」按钮 → 跳转 `/diagnosis/{id}`

**Step 2: Commit**

```bash
git add frontend/src/app/\(main\)/requirements/
git commit -m "feat(frontend): implement P2 requirement detail page"
```

---

## Task 17: 最终验证

**Step 1: 后端 lint + 类型检查**

```bash
cd backend
uv run ruff check . && uv run ruff format .
uv run pyright app/
```

**Step 2: 前端 lint + 类型检查**

```bash
cd frontend
bunx biome check --write .
bunx tsc --noEmit
```

**Step 3: 端到端流程验证**

1. 访问 `http://localhost:3000` → 项目列表显示
2. 点击项目 → 需求列表
3. 点击需求 → 需求详情，点「开始健康诊断」
4. 健康诊断页面 → ThinkingStream 逐字渲染思考过程，内容区显示 AI 分析
5. 进入测试点确认 → 点「AI 生成」→ SSE 流显示
6. 进入生成工作台 → 发送消息 → 用例逐步生成
7. 进入用例管理 → 列表显示已生成用例

**Step 4: 最终 Commit**

```bash
git add -A
git commit -m "feat: complete phase-1 core workflow implementation"
```

---

## 快速参考

| 命令 | 用途 |
|------|------|
| `cd backend && uv run uvicorn app.main:app --reload` | 启动后端 |
| `cd frontend && bun dev` | 启动前端 |
| `uv run alembic upgrade head` | 执行数据库迁移 |
| `uv run ruff check . && uv run ruff format .` | 后端 lint |
| `bunx biome check --write .` | 前端 lint |
| `bunx tsc --noEmit` | 前端类型检查 |
| `http://localhost:8000/docs` | FastAPI Swagger UI |
