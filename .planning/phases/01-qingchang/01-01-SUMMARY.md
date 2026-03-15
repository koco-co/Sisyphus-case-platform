---
phase: 01-qingchang
plan: "01"
subsystem: infra
tags: [fastapi, router, nextjs, app-router, module-cleanup]

# Dependency graph
requires: []
provides:
  - "/api/test-plans/* 路由已从注册表移除，访问返回 404"
  - "/api/collaboration/* 路由已从注册表移除，访问返回 404"
  - "前端 /review 路由目录已删除"
affects:
  - 02-zhulianzid
  - Phase 2 主链路重构

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "_MODULE_NAMES 列表是后端路由注册的唯一控制点，移除条目即可屏蔽对应路由而无需删除模块文件"

key-files:
  created: []
  modified:
    - backend/app/main.py

key-decisions:
  - "仅移除路由注册，保留模块文件和 DB 表，为将来可能的数据迁移保留退路"
  - "前端删除整个 /review 目录而非仅禁用链接，彻底消除路由噪声"

patterns-established:
  - "模块裁剪 = 从 _MODULE_NAMES 删除条目，不删除模块文件，不执行 DB 迁移"

requirements-completed:
  - MOD-01
  - MOD-02

# Metrics
duration: 2min
completed: 2026-03-15
---

# Phase 01 Plan 01: 清场 — M09/M18 路由裁剪 Summary

**从 FastAPI _MODULE_NAMES 移除 test_plan 和 collaboration，删除前端 /review 目录，屏蔽废弃模块路由而保留 DB 表和模块文件**

## Performance

- **Duration:** 2min
- **Started:** 2026-03-15T09:50:25Z
- **Completed:** 2026-03-15T09:52:58Z
- **Tasks:** 2
- **Files modified:** 1 modified + 1 deleted (1 directory removed)

## Accomplishments

- 从 `_MODULE_NAMES` 列表移除 `"test_plan"` 和 `"collaboration"` 两个条目，对应路由不再注册
- 删除 `frontend/src/app/(main)/review/` 目录（含 1 个文件），消除前端 /review 路由
- 确认无跨模块引用（其他模块无 import test_plan/collaboration），无需额外清理

## Task Commits

1. **Task 1: 从 _MODULE_NAMES 移除 test_plan 和 collaboration** - `6e2be01` (chore)
2. **Task 2: 删除前端协作审阅页面目录** - `485aefd` (chore)

## Files Created/Modified

- `backend/app/main.py` - 从 _MODULE_NAMES 列表删除 "test_plan" 和 "collaboration" 两行
- `frontend/src/app/(main)/review/[token]/page.tsx` - 已删除（连同父目录）

## Decisions Made

- 保留 `backend/app/modules/test_plan/` 和 `backend/app/modules/collaboration/` 目录完整，不执行 Alembic 迁移，保留 DB 表。理由：裁剪仅针对路由暴露，历史数据和模块代码保留退路。

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- M09/M18 路由屏蔽完成，Phase 2 主链路重构不会受这两个废弃模块的路由冲突干扰
- 无阻塞项

---
*Phase: 01-qingchang*
*Completed: 2026-03-15*
