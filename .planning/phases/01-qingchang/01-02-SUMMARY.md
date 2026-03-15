---
phase: 01-qingchang
plan: 02
subsystem: ui
tags: [notification, cleanup, fastapi, nextjs, sonner]

# Dependency graph
requires: []
provides:
  - M16 通知模块后端路由已注销（_MODULE_NAMES 移除 notification）
  - NotificationBell 前端组件已删除
  - /notifications 页面路由已删除
  - 孤儿 useNotifications hook 和 notifications-store 已删除
  - api.ts 中 notificationsApi 和 NotificationRecord 已移除
  - sonner Toaster 全局挂载保留完好
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "通知需求通过 sonner toast() 全局 Toaster 满足，无需专用通知中心组件"

key-files:
  created: []
  modified:
    - backend/app/main.py
    - frontend/src/app/(main)/layout.tsx
    - frontend/src/app/(main)/layout.test.tsx
    - frontend/src/lib/api.ts
  deleted:
    - frontend/src/app/(main)/notifications/page.tsx
    - frontend/src/components/ui/NotificationBell.tsx
    - frontend/src/hooks/useNotifications.ts
    - frontend/src/stores/notifications-store.ts

key-decisions:
  - "M16 通知模块完全裁剪，用 sonner toast() 替代通知中心，降低系统复杂度"
  - "孤儿 hook/store 文件（useNotifications、notifications-store）随组件一并删除，避免死代码积累"

patterns-established:
  - "裁剪模块时同步清理所有孤儿依赖文件（hook、store、api client）"

requirements-completed:
  - MOD-03

# Metrics
duration: 15min
completed: 2026-03-15
---

# Phase 1 Plan 02: M16 通知模块清场 Summary

**注销 M16 通知后端路由、删除 NotificationBell 组件及 /notifications 页面、清理孤儿 hook/store/api，保留 sonner Toaster 全局通知机制**

## Performance

- **Duration:** 15 min
- **Started:** 2026-03-15T00:00:00Z
- **Completed:** 2026-03-15T00:15:00Z
- **Tasks:** 1
- **Files modified:** 4 modified, 4 deleted

## Accomplishments
- 后端 `_MODULE_NAMES` 移除 `notification`，/api/notifications/* 路由不再注册
- 前端删除 `NotificationBell.tsx` 组件和 `/notifications` 页面目录
- `layout.tsx` 移除 NotificationBell import 和 JSX，`layout.test.tsx` 同步移除 mock
- 孤儿 `useNotifications` hook、`notifications-store`、`notificationsApi`、`NotificationRecord` 类型全部清除
- TypeScript 编译通过（无错误）

## Task Commits

Each task was committed atomically:

1. **Task 1: 注销通知后端路由并清理前端组件和页面** - `615465d` (refactor)

**Auto-fix (Rule 1 - 孤儿代码清理):** `30fcc97` (refactor)

## Files Created/Modified
- `backend/app/main.py` - 从 `_MODULE_NAMES` 移除 `"notification"`
- `frontend/src/app/(main)/layout.tsx` - 移除 NotificationBell import 和 `<NotificationBell />` JSX
- `frontend/src/app/(main)/layout.test.tsx` - 移除 NotificationBell mock 块
- `frontend/src/lib/api.ts` - 移除 `NotificationRecord` 接口和 `notificationsApi` 对象
- `frontend/src/app/(main)/notifications/page.tsx` - 已删除
- `frontend/src/components/ui/NotificationBell.tsx` - 已删除
- `frontend/src/hooks/useNotifications.ts` - 已删除
- `frontend/src/stores/notifications-store.ts` - 已删除

## Decisions Made
- M16 通知模块整体裁剪，不保留任何通知中心 UI，sonner toast() 满足实时通知需求
- 删除 NotificationBell 后发现三个孤儿文件（hook/store/api），一并清理避免死代码

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] 清理因删除 NotificationBell 产生的孤儿代码**
- **Found during:** Task 1（验证阶段发现 NotificationBell 已被删除但其依赖仍存在）
- **Issue:** `useNotifications.ts`、`notifications-store.ts`、`api.ts` 中的 `notificationsApi` 和 `NotificationRecord` 在 NotificationBell 删除后无任何调用方，成为死代码
- **Fix:** 删除 hook 和 store 文件，从 `api.ts` 移除对应接口和 API 客户端对象
- **Files modified:** `frontend/src/lib/api.ts`（删除 16 行），删除 `useNotifications.ts`、`notifications-store.ts`
- **Verification:** TypeScript 编译通过，`grep -rn "notificationsApi"` 无结果
- **Committed in:** `30fcc97`

---

**Total deviations:** 1 auto-fixed (Rule 1 - 孤儿死代码清理)
**Impact on plan:** 必要清理，防止 TypeScript 孤立导出积累。无范围蔓延。

## Issues Encountered
- `.next/` 缓存中 `validator.ts` 引用了已删除的 notifications page，导致首次 `tsc --noEmit` 报错。清除 `.next/` 目录后重新编译即通过。

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- M16 清场完成，后续 Phase 2 主链路重构不受通知模块干扰
- sonner Toaster 全局可用，任何模块均可直接调用 `toast()` 发送通知

---
*Phase: 01-qingchang*
*Completed: 2026-03-15*
