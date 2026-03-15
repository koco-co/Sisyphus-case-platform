import uuid

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.core.dependencies import AsyncSessionDep
from app.modules.generation.schemas import GeneratedCaseResponse, GeneratedCaseStepResponse
from app.modules.generation.service import GenerationService
from app.modules.testcases.models import TestCase

router = APIRouter(prefix="/generation", tags=["generation"])


# ── RAG Preview (RAG-05) ─────────────────────────────────────────


class RagPreviewResult(BaseModel):
    title: str
    content: str
    score: float


class RagPreviewResponse(BaseModel):
    results: list[RagPreviewResult]


class CreateSessionRequest(BaseModel):
    requirement_id: uuid.UUID
    mode: str = "test_point_driven"


class ChatRequest(BaseModel):
    message: str


class TemplateGenerateRequest(BaseModel):
    requirement_id: uuid.UUID
    template_id: uuid.UUID
    variables: dict[str, str] | None = None


def _normalize_case_type(case_type: str) -> str:
    return "normal" if case_type == "functional" else case_type


def _normalize_steps(steps: object) -> list[GeneratedCaseStepResponse]:
    normalized: list[GeneratedCaseStepResponse] = []
    if not isinstance(steps, list):
        return normalized

    for index, step in enumerate(steps, start=1):
        if not isinstance(step, dict):
            continue
        normalized.append(
            GeneratedCaseStepResponse(
                step_num=step.get("step_num") or step.get("step") or index,
                action=step.get("action", ""),
                expected_result=step.get("expected_result") or step.get("expected", ""),
            )
        )

    return normalized


def _serialize_case(test_case: TestCase) -> GeneratedCaseResponse:
    return GeneratedCaseResponse(
        id=test_case.id,
        case_id=test_case.case_id,
        title=test_case.title,
        priority=test_case.priority,
        case_type=_normalize_case_type(test_case.case_type),
        status=test_case.status,
        steps=_normalize_steps(getattr(test_case, "steps", [])),
    )


@router.post("/sessions")
async def create_session(data: CreateSessionRequest, session: AsyncSessionDep) -> dict:
    svc = GenerationService(session)
    gen_session = await svc.get_or_create_session(data.requirement_id, data.mode)
    return {
        "id": str(gen_session.id),
        "requirement_id": str(gen_session.requirement_id),
        "mode": gen_session.mode,
        "status": gen_session.status,
    }


@router.get("/sessions/by-requirement/{requirement_id}")
async def list_sessions(requirement_id: uuid.UUID, session: AsyncSessionDep) -> list[dict]:
    svc = GenerationService(session)
    sessions = await svc.list_sessions(requirement_id)
    return [
        {
            "id": str(s.id),
            "requirement_id": str(s.requirement_id),
            "mode": s.mode,
            "status": s.status,
            "created_at": s.created_at.isoformat() if s.created_at else "",
        }
        for s in sessions
    ]


@router.get("/sessions/{session_id}/messages")
async def list_messages(session_id: uuid.UUID, session: AsyncSessionDep) -> list[dict]:
    svc = GenerationService(session)
    return await svc.list_messages_with_cases(session_id)


@router.post("/sessions/{session_id}/chat")
async def chat(session_id: uuid.UUID, data: ChatRequest, session: AsyncSessionDep) -> StreamingResponse:
    svc = GenerationService(session)
    try:
        collector = await svc.chat_and_persist_stream(session_id, data.message)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return StreamingResponse(collector, media_type="text/event-stream")


@router.get("/sessions/{session_id}/cases", response_model=list[GeneratedCaseResponse])
async def list_session_cases(
    session_id: uuid.UUID,
    session: AsyncSessionDep,
) -> list[GeneratedCaseResponse]:
    svc = GenerationService(session)
    cases = await svc.list_session_cases(session_id)
    return [_serialize_case(case) for case in cases]


@router.post("/sessions/{session_id}/cases/{case_id}/accept", response_model=GeneratedCaseResponse)
async def accept_session_case(
    session_id: uuid.UUID,
    case_id: uuid.UUID,
    session: AsyncSessionDep,
) -> GeneratedCaseResponse:
    svc = GenerationService(session)
    try:
        case = await svc.accept_session_case(session_id, case_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _serialize_case(case)


@router.post("/by-requirement/{requirement_id}/chat")
async def chat_by_requirement(
    requirement_id: uuid.UUID,
    data: ChatRequest,
    session: AsyncSessionDep,
) -> StreamingResponse:
    """Chat endpoint that auto-creates a generation session if none exists."""
    svc = GenerationService(session)
    collector = await svc.chat_by_requirement_and_persist_stream(requirement_id, data.message)
    return StreamingResponse(collector, media_type="text/event-stream")


@router.post("/from-template")
async def generate_from_template(
    data: TemplateGenerateRequest,
    session: AsyncSessionDep,
) -> StreamingResponse:
    """基于模板生成测试用例（模板驱动模式）。"""
    svc = GenerationService(session)
    try:
        collector = await svc.template_and_persist_stream(data.requirement_id, data.template_id, data.variables)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return StreamingResponse(collector, media_type="text/event-stream")


@router.get("/rag-preview", response_model=RagPreviewResponse)
async def rag_preview(
    query: str = Query(..., description="检索查询文本"),
    product: str | None = Query(None, description="可选的产品名称过滤"),
) -> RagPreviewResponse:
    """检索相似历史用例，返回 top-5 结果（相似度 >= 0.72）。

    供工作台 Step1 RAG 预览面板调用。
    """
    from app.engine.rag.retriever import retrieve_similar_cases

    try:
        results = await retrieve_similar_cases(
            query,
            top_k=5,
            score_threshold=0.72,
            product=product,
        )
        return RagPreviewResponse(results=[
            RagPreviewResult(
                title=r.metadata.get("title", ""),
                content=r.content,
                score=r.score,
            )
            for r in results
        ])
    except Exception:
        # 任何异常（包括 Qdrant 连接失败）都返回空结果，保证 graceful degradation
        return RagPreviewResponse(results=[])
