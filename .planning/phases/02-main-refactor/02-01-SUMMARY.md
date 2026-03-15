---
phase: 02-main-refactor
plan: "01"
subsystem: api
tags: [fastapi, sqlalchemy, alembic, qdrant, rag, tdd, diagnosis, scene_map]

requires:
  - phase: 01-qingchang
    provides: cleaned module stubs and M03/M04 baseline router/service/model files

provides:
  - "PATCH /diagnosis/risks/{risk_id}/confirm endpoint (returns confirmed=true, idempotent)"
  - "DiagnosisRisk.confirmed boolean column in DB (default false, migrated)"
  - "POST /scene-map/{req_id}/rag-preview endpoint with Qdrant graceful degradation"
  - "SceneMapService.get_test_points_by_ids() method"

affects:
  - 02-02-ANA-07 (frontend confirm risk button depends on this endpoint)
  - 02-03-WRK-04 (frontend RAG preview panel depends on this endpoint)

tech-stack:
  added: []
  patterns:
    - "Endpoint-level Qdrant graceful degradation: try/except returning empty list on any exception"
    - "Idempotent confirm pattern: set boolean=True then flush+refresh, safe to call multiple times"
    - "TDD RED→GREEN: write failing test first, then implement minimal code to pass"

key-files:
  created:
    - backend/alembic/versions/4bf80568fe2c_add_confirmed_to_diagnosis_risks.py
    - backend/tests/unit/test_scene_map/test_rag_preview.py
  modified:
    - backend/app/modules/diagnosis/models.py
    - backend/app/modules/diagnosis/schemas.py
    - backend/app/modules/diagnosis/service.py
    - backend/app/modules/diagnosis/router.py
    - backend/app/modules/scene_map/schemas.py
    - backend/app/modules/scene_map/service.py
    - backend/app/modules/scene_map/router.py
    - backend/tests/unit/test_diagnosis/test_diagnosis_api.py

key-decisions:
  - "Alembic autogenerate migration trimmed: removed unrelated table-drop noise, kept only confirmed column addition"
  - "RAG preview endpoint catches all exceptions (not just ConnectionError) to guarantee graceful degradation against any Qdrant issue"
  - "confirm_risk uses flush+refresh instead of commit to allow service-layer transaction control"

patterns-established:
  - "Pattern 1: RAG endpoint wraps retriever call in try/except returning empty results — Qdrant unavailability never propagates as 500"
  - "Pattern 2: TDD test mocks use datetime.now(timezone.utc) for created_at/updated_at to satisfy BaseResponse schema"

requirements-completed: [ANA-07, WRK-04]

duration: 35min
completed: 2026-03-15
---

# Phase 2 Plan 01: Backend Foundation Summary

**DiagnosisRisk confirmed column + PATCH confirm endpoint + POST rag-preview endpoint with Qdrant graceful degradation**

## Performance

- **Duration:** ~35 min
- **Started:** 2026-03-15T20:00:00Z
- **Completed:** 2026-03-15T20:35:00Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments

- Added `confirmed` boolean column to `diagnosis_risks` table with Alembic migration (server_default=false)
- PATCH /diagnosis/risks/{risk_id}/confirm endpoint: returns 200+confirmed=true, 404 for missing, idempotent
- POST /scene-map/{req_id}/rag-preview endpoint: returns similar historical test cases, gracefully returns empty list when Qdrant is unreachable
- TDD: both tasks written test-first, 56 tests passing across diagnosis + scene_map modules

## Task Commits

1. **Task 1: DiagnosisRisk.confirmed + DB migration + confirm endpoint** - `1821268` (feat)
2. **Task 2: RAG 历史用例预览端点 (WRK-04)** - `323fd7d` (feat)

## Files Created/Modified

- `backend/app/modules/diagnosis/models.py` - Added confirmed: Mapped[bool] column
- `backend/app/modules/diagnosis/schemas.py` - Added confirmed: bool = False to DiagnosisRiskResponse
- `backend/app/modules/diagnosis/service.py` - Added confirm_risk() method
- `backend/app/modules/diagnosis/router.py` - Added PATCH /risks/{risk_id}/confirm endpoint
- `backend/alembic/versions/4bf80568fe2c_add_confirmed_to_diagnosis_risks.py` - DB migration (trimmed)
- `backend/app/modules/scene_map/schemas.py` - Added RagPreviewRequest/Result/Response schemas
- `backend/app/modules/scene_map/service.py` - Added get_test_points_by_ids() method
- `backend/app/modules/scene_map/router.py` - Added POST /{req_id}/rag-preview endpoint
- `backend/tests/unit/test_diagnosis/test_diagnosis_api.py` - Added 3 confirm risk TDD tests
- `backend/tests/unit/test_scene_map/test_rag_preview.py` - Created with 3 RAG preview TDD tests

## Decisions Made

- Alembic autogenerate produced a noisy migration with many unrelated table DROPs; trimmed to only the confirmed column addition to avoid FK dependency failures
- RAG preview catches broad `Exception` (not just ConnectionError) to handle all Qdrant failure modes
- `confirm_risk()` uses `flush()` not `commit()` for proper session lifecycle management

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Alembic migration trimmed to remove unrelated table DROPs**
- **Found during:** Task 1 (alembic upgrade head)
- **Issue:** autogenerate detected stale Phase 1 table removals; `DROP TABLE reviews` failed due to FK from `review_decisions`
- **Fix:** Replaced the full autogenerate migration with a minimal migration containing only `op.add_column('diagnosis_risks', confirmed)`
- **Files modified:** `backend/alembic/versions/4bf80568fe2c_add_confirmed_to_diagnosis_risks.py`
- **Verification:** `uv run alembic upgrade head` succeeds; column exists in DB
- **Committed in:** 1821268 (Task 1 commit)

**2. [Rule 1 - Bug] Test mock missing datetime for BaseResponse validation**
- **Found during:** Task 1 GREEN phase (first pytest run)
- **Issue:** `DiagnosisRiskResponse.model_validate(mock)` failed because mock `created_at=None` but schema requires `datetime`
- **Fix:** Added `from datetime import datetime, timezone` import and set `mock_risk.created_at = datetime.now(timezone.utc)` in test fixtures
- **Files modified:** `backend/tests/unit/test_diagnosis/test_diagnosis_api.py`
- **Verification:** All 5 diagnosis API tests pass
- **Committed in:** 1821268 (Task 1 commit)

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 bug)
**Impact on plan:** Both fixes were required for execution correctness. No scope creep.

## Issues Encountered

None beyond the two auto-fixed deviations above.

## Next Phase Readiness

- `PATCH /diagnosis/risks/{id}/confirm` is ready for 02-02 (ANA-07 frontend confirm button)
- `POST /scene-map/{req_id}/rag-preview` is ready for 02-03 (WRK-04 RAG preview panel)
- All 56 diagnosis + scene_map tests green, ruff lint clean

---
*Phase: 02-main-refactor*
*Completed: 2026-03-15*
