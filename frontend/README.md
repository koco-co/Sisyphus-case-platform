# Sisyphus-Y Frontend

AI 驱动的企业级功能测试用例自动生成平台 — 前端应用

## 技术栈

- **框架**: Next.js 16 (App Router) + TypeScript 5
- **样式**: Tailwind CSS 4 + sy-* 设计 Token（禁止硬编码色值）
- **组件库**: shadcn/ui + Sonner (Toast)
- **状态管理**: Zustand + TanStack React Query
- **可视化**: React Flow (场景地图) / Recharts (质量看板)
- **图标**: lucide-react（禁止 emoji 作 UI 元素）
- **代码质量**: Biome (lint + format) + TypeScript strict
- **包管理**: bun（禁止 npm/yarn/pnpm）

## 开发

```bash
bun install          # 安装依赖
bun dev              # 开发服务器 → http://localhost:3000
bun run build        # 生产构建
bunx tsc --noEmit    # 类型检查
bunx biome check .   # lint + format 检查
```

## 目录结构

```
src/
├── app/
│   ├── (auth)/              # 登录等无鉴权页面
│   └── (main)/              # 主业务页面（9个菜单入口）
│       ├── page.tsx          # 仪表盘（概览 + 质量分析）
│       ├── analysis/         # 分析台（需求/AI分析/场景地图/覆盖）
│       ├── workbench/        # 工作台（测试点确认 + 用例生成）
│       ├── diff/             # 需求Diff（文本对比 + 变更摘要）
│       ├── testcases/        # 用例库（目录树 + 导入导出）
│       ├── templates/        # 模板库（结构模板 + Prompt模板）
│       ├── knowledge/        # 知识库（4分类管理）
│       ├── recycle/          # 回收站（30天自动清理）
│       └── settings/         # 设置（AI配置/Prompt/日志）
├── components/
│   ├── ui/                   # 基础组件（FormDialog, StatusBadge等）
│   ├── layout/               # 布局组件（ThreeColLayout等）
│   └── workspace/            # 工作台组件（CaseCard, StreamCursor等）
├── hooks/                    # 自定义 Hooks
├── lib/                      # 工具函数（api.ts, utils.ts）
└── stores/                   # Zustand 状态管理
```

## 设计规范

- 所有颜色使用 `sy-*` Token（如 `text-sy-accent`、`bg-sy-bg-2`）
- 禁止硬编码色值（如 `text-[#00d9a3]` 或 `style={{ color: '#00d9a3' }}`）
- 全局框架：顶部水平导航栏（49px）+ 内容区
- 三栏工作台：左栏(固定宽) + 中栏(flex-1) + 右栏(固定宽)，各列独立滚动
