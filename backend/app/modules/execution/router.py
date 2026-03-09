import uuid

from fastapi import APIRouter

from app.core.dependencies import AsyncSessionDep
from app.modules.execution.schemas import (
    BatchExecutionRequest,
    ExecutionResultCreate,
    ExecutionResultResponse,
    ExecutionSummaryResponse,
    JiraSyncRequest,
    JiraSyncResponse,
    MarkFailedRequest,
    RAGWeightAdjustRequest,
    RAGWeightAdjustResponse,
)
from app.modules.execution.service import ExecutionService

router = APIRouter(prefix="/execution", tags=["execution"])


@router.post("", response_model=ExecutionResultResponse, status_code=201)
async def record_result(data: ExecutionResultCreate, session: AsyncSessionDep) -> ExecutionResultResponse:
    svc = ExecutionService(session)
    result = await svc.record_result(data)
    return ExecutionResultResponse.model_validate(result)


@router.post("/batch", response_model=list[ExecutionResultResponse])
async def batch_import_results(data: BatchExecutionRequest, session: AsyncSessionDep) -> list[ExecutionResultResponse]:
    svc = ExecutionService(session)
    results = await svc.batch_import_results(data.results)
    return [ExecutionResultResponse.model_validate(r) for r in results]


@router.get("/summary/{iteration_id}", response_model=ExecutionSummaryResponse)
async def get_execution_summary(iteration_id: uuid.UUID, session: AsyncSessionDep) -> ExecutionSummaryResponse:
    svc = ExecutionService(session)
    summary = await svc.get_execution_summary(iteration_id)
    return ExecutionSummaryResponse(**summary)


@router.get("/history/{case_id}", response_model=list[ExecutionResultResponse])
async def get_case_history(case_id: uuid.UUID, session: AsyncSessionDep) -> list[ExecutionResultResponse]:
    svc = ExecutionService(session)
    results = await svc.get_case_history(case_id)
    return [ExecutionResultResponse.model_validate(r) for r in results]


@router.post("/mark-failed", response_model=ExecutionResultResponse, status_code=201)
async def mark_failed(data: MarkFailedRequest, session: AsyncSessionDep) -> ExecutionResultResponse:
    svc = ExecutionService(session)
    result = await svc.mark_failed(
        test_case_id=data.test_case_id,
        iteration_id=data.iteration_id,
        defect_id=data.defect_id,
        actual_result=data.actual_result,
    )
    return ExecutionResultResponse.model_validate(result)


@router.get("/failed/{iteration_id}", response_model=list[ExecutionResultResponse])
async def list_failed_cases(iteration_id: uuid.UUID, session: AsyncSessionDep) -> list[ExecutionResultResponse]:
    svc = ExecutionService(session)
    results = await svc.get_failed_cases(iteration_id)
    return [ExecutionResultResponse.model_validate(r) for r in results]


# ── RAG Weight Adjustment (B-M13-04) ──────────────────────────────


@router.post("/adjust-rag-weights", response_model=RAGWeightAdjustResponse)
async def adjust_rag_weights(data: RAGWeightAdjustRequest, session: AsyncSessionDep) -> RAGWeightAdjustResponse:
    svc = ExecutionService(session)
    result = await svc.adjust_rag_weights([item.model_dump() for item in data.execution_results])
    return RAGWeightAdjustResponse(**result)


# ── Jira/Xray Results Sync (B-M13-06) ────────────────────────────


@router.post("/sync-jira", response_model=JiraSyncResponse)
async def sync_results_to_jira(data: JiraSyncRequest, session: AsyncSessionDep) -> JiraSyncResponse:
    svc = ExecutionService(session)
    result = await svc.sync_results_to_jira(data.case_ids, data.jira_config.model_dump())
    return JiraSyncResponse(**result)
