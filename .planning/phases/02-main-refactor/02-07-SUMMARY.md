---
phase: 02-main-refactor
plan: "07"
subsystem: ui
tags: [workbench, test-points, fold-threshold, TestPointGroupList]

# Dependency graph
requires:
  - phase: 02-main-refactor
    provides: TestPointGroupList component with FOLD_THRESHOLD=5 fold logic
provides:
  - WRK-02 gap closed: workbench Step1 uses TestPointGroupList with group fold / expand-more / inline-add
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns: []

key-files:
  created: []
  modified:
    - frontend/src/app/(main)/workbench/page.tsx

key-decisions:
  - "workbench/page.tsx onAdd adapter: construct full Omit<TestPointItem,'id'> object because sm.addPoint takes a structured payload, not (title, groupName) positional args"
  - "Removed duplicate start/append-generate button from Step1 header — TestPointGroupList bottom bar already provides it"

patterns-established: []

requirements-completed:
  - WRK-02

# Metrics
duration: 6min
completed: 2026-03-15
---

# Phase 02 Plan 07: TestPointGroupList in Workbench Step1 Summary

**Wired orphan TestPointGroupList into workbench Step1 mid-column, activating FOLD_THRESHOLD=5 group fold, expand-more, and inline-add-point for WRK-02**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-15T13:24:34Z
- **Completed:** 2026-03-15T13:31:30Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments

- Replaced `TestPointList` with `TestPointGroupList` in workbench Step1 mid-column
- Removed duplicate start/append-generate button from Step1 header (now provided by `TestPointGroupList` bottom bar)
- Biome lint and TypeScript type check both pass with zero errors

## Task Commits

1. **Task 1: Replace TestPointList with TestPointGroupList** - `afaff22` (feat)

## Files Created/Modified

- `frontend/src/app/(main)/workbench/page.tsx` - Replaced TestPointList JSX with TestPointGroupList, updated import, removed duplicate generate button, fixed onAdd adapter

## Decisions Made

- `sm.addPoint` actual signature is `async (point: Omit<TestPointItem, 'id'>)` — plan's assumed `(title, groupName)` shorthand was incorrect. Fixed `onAdd` lambda to construct the full payload inline.
- Duplicate header button removed rather than hidden — TestPointGroupList's built-in bottom bar is the canonical generate action for WRK-02.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed sm.addPoint call signature mismatch**
- **Found during:** Task 1 (TypeScript type check)
- **Issue:** Plan specified `sm.addPoint(title, groupName)` but actual hook signature is `async (point: Omit<TestPointItem,'id'>)`. TS error TS2554: Expected 1 arguments, but got 2.
- **Fix:** Changed `onAdd` adapter to construct `{ group_name, title, description: null, source: 'pending', status: 'pending', priority: 'medium', estimated_cases: 0 }` object
- **Files modified:** frontend/src/app/(main)/workbench/page.tsx
- **Verification:** `bunx tsc --noEmit` — no errors; `bunx biome check` — no errors
- **Committed in:** afaff22 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - type/signature bug)
**Impact on plan:** Required fix for correctness; no scope change.

## Issues Encountered

None beyond the signature mismatch above.

## Next Phase Readiness

- WRK-02 gap closed; workbench Step1 fold behavior is live
- No outstanding blockers

---
*Phase: 02-main-refactor*
*Completed: 2026-03-15*
