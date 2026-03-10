import logging
import uuid

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.ai.parser import parse_test_cases
from app.ai.sse_collector import SSECollector
from app.core.dependencies import AsyncSessionDep
from app.modules.generation.schemas import GeneratedCaseResponse, GeneratedCaseStepResponse
from app.modules.generation.service import GenerationService
from app.modules.testcases.models import TestCase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/generation", tags=["generation"])


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


async def _save_and_parse(
    session_id: uuid.UUID,
    requirement_id: uuid.UUID,
    full_text: str,
) -> None:
    """Persist assistant message and auto-parse test cases from AI output."""
    from app.core.database import get_async_session_context
    from app.modules.testcases.schemas import TestCaseCreate, TestCaseStepSchema
    from app.modules.testcases.service import TestCaseService

    async with get_async_session_context() as new_session:
        gen_svc = GenerationService(new_session)
        await gen_svc.save_message(session_id, "assistant", full_text)

        parsed = parse_test_cases(full_text)
        if not parsed:
            return

        tc_svc = TestCaseService(new_session)
        for case in parsed:
            try:
                steps = [
                    TestCaseStepSchema(
                        step=step.get("step_num", i + 1),
                        action=step.get("action", ""),
                        expected=step.get("expected_result", ""),
                    )
                    for i, step in enumerate(case.get("steps", []))
                ]
                case_type_raw = case.get("case_type", "functional")
                valid_types = {"functional", "boundary", "exception", "performance", "security", "compatibility"}
                case_type = case_type_raw if case_type_raw in valid_types else "functional"

                data = TestCaseCreate(
                    requirement_id=requirement_id,
                    generation_session_id=session_id,
                    title=case.get("title", ""),
                    priority=case.get("priority", "P1"),
                    case_type=case_type,  # type: ignore[arg-type]
                    precondition=case.get("precondition", ""),
                    source="ai_generated",
                    steps=steps,
                )
                await tc_svc.create_case(data)
            except Exception:
                logger.warning("Failed to save parsed test case: %s", case.get("title", ""))


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
    messages = await svc.list_messages(session_id)
    return [
        {
            "id": str(m.id),
            "role": m.role,
            "content": m.content,
            "thinking_content": m.thinking_content,
            "created_at": m.created_at.isoformat() if m.created_at else "",
        }
        for m in messages
    ]


@router.post("/sessions/{session_id}/chat")
async def chat(session_id: uuid.UUID, data: ChatRequest, session: AsyncSessionDep) -> StreamingResponse:
    svc = GenerationService(session)
    gen_session = await svc.get_session(session_id)
    if not gen_session:
        raise HTTPException(status_code=404, detail="Session not found")
    await svc.save_message(session_id, "user", data.message)
    stream = await svc.chat_stream(session_id, data.message)

    sid = session_id
    req_id = gen_session.requirement_id

    async def on_complete(full_text: str) -> None:
        await _save_and_parse(sid, req_id, full_text)

    collector = SSECollector(stream, on_complete=on_complete)
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
    gen_session = await svc.get_or_create_session(requirement_id)
    sid = gen_session.id

    await svc.save_message(sid, "user", data.message)
    stream = await svc.chat_stream(sid, data.message)

    async def on_complete(full_text: str) -> None:
        await _save_and_parse(sid, requirement_id, full_text)

    collector = SSECollector(stream, on_complete=on_complete)
    return StreamingResponse(collector, media_type="text/event-stream")


@router.post("/from-template")
async def generate_from_template(
    data: TemplateGenerateRequest,
    session: AsyncSessionDep,
) -> StreamingResponse:
    """基于模板生成测试用例（模板驱动模式）。"""
    import json

    from sqlalchemy import select

    from app.engine.case_gen.template_driven import template_driven_stream
    from app.modules.products.models import Requirement
    from app.modules.templates.models import TestCaseTemplate

    tpl_q = select(TestCaseTemplate).where(
        TestCaseTemplate.id == data.template_id,
        TestCaseTemplate.deleted_at.is_(None),
    )
    tpl_result = await session.execute(tpl_q)
    template = tpl_result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    req = await session.get(Requirement, data.requirement_id)
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found")

    req_content = json.dumps(req.content_ast, ensure_ascii=False) if req.content_ast else ""

    svc = GenerationService(session)
    gen_session = await svc.get_or_create_session(data.requirement_id, mode="template_driven")
    sid = gen_session.id

    stream = await template_driven_stream(
        template_name=template.name,
        template_category=template.category,
        template_description=template.description or "",
        template_content=template.template_content,
        template_variables=template.variables,
        user_variables=data.variables,
        requirement_title=req.title,
        requirement_content=req_content,
    )

    async def on_complete(full_text: str) -> None:
        await _save_and_parse(sid, data.requirement_id, full_text)

    collector = SSECollector(stream, on_complete=on_complete)
    return StreamingResponse(collector, media_type="text/event-stream")
