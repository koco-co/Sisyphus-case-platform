import uuid

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.ai.sse_collector import SSECollector
from app.core.database import get_async_session_context
from app.core.dependencies import AsyncSessionDep
from app.modules.diagnosis.schemas import (
    ChatRequest,
    DiagnosisReportResponse,
    DiagnosisRiskResponse,
    DiagnosisRiskUpdate,
)
from app.modules.diagnosis.service import DiagnosisService

router = APIRouter(prefix="/diagnosis", tags=["diagnosis"])


@router.get("/reports/{requirement_id}")
async def get_report_status(requirement_id: uuid.UUID, session: AsyncSessionDep) -> dict:
    """Check whether a diagnosis report exists for a requirement."""
    svc = DiagnosisService(session)
    report = await svc.get_report(requirement_id)
    if not report:
        return {"exists": False, "requirement_id": str(requirement_id)}
    return {
        "exists": True,
        "requirement_id": str(requirement_id),
        "report_id": str(report.id),
        "status": report.status,
        "summary": report.summary,
        "created_at": report.created_at.isoformat() if report.created_at else "",
    }


@router.get("/{requirement_id}", response_model=DiagnosisReportResponse)
async def get_diagnosis(requirement_id: uuid.UUID, session: AsyncSessionDep) -> DiagnosisReportResponse:
    svc = DiagnosisService(session)
    report = await svc.get_report(requirement_id)
    if not report:
        raise HTTPException(status_code=404, detail="DiagnosisReport not found")
    risks = await svc.list_risks(report.id)
    resp = DiagnosisReportResponse.model_validate(report)
    resp.risks = [DiagnosisRiskResponse.model_validate(r) for r in risks]
    return resp


@router.post("/{requirement_id}/run")
async def run_diagnosis(requirement_id: uuid.UUID, session: AsyncSessionDep) -> StreamingResponse:
    svc = DiagnosisService(session)
    report = await svc.create_or_get_report(requirement_id)
    report_id = report.id

    stream = await svc.run_stream(requirement_id)

    async def on_complete(full_text: str) -> None:
        async with get_async_session_context() as new_session:
            new_svc = DiagnosisService(new_session)
            # 自动解析 AI 响应并持久化（消息 + 风险项 + 报告更新）
            await new_svc.persist_ai_response(report_id, full_text, round_num=1)
            await new_svc.complete_report(report_id, summary=full_text)

    collector = SSECollector(stream, on_complete=on_complete)
    return StreamingResponse(collector, media_type="text/event-stream")


@router.post("/{requirement_id}/chat")
async def chat_diagnosis(
    requirement_id: uuid.UUID,
    data: ChatRequest,
    session: AsyncSessionDep,
) -> StreamingResponse:
    svc = DiagnosisService(session)
    report = await svc.create_or_get_report(requirement_id)
    report_id = report.id
    user_message = data.message

    stream = await svc.chat_stream(requirement_id, user_message)

    async def on_complete(full_text: str) -> None:
        async with get_async_session_context() as new_session:
            new_svc = DiagnosisService(new_session)
            round_num = await new_svc.get_current_round(report_id)
            await new_svc.save_message(report_id, "user", user_message, round_num=round_num)
            # 自动解析 AI 响应并持久化（消息 + 风险项）
            await new_svc.persist_ai_response(report_id, full_text, round_num=round_num)

    collector = SSECollector(stream, on_complete=on_complete)
    return StreamingResponse(collector, media_type="text/event-stream")


@router.post("/{requirement_id}/create", response_model=DiagnosisReportResponse)
async def create_report(requirement_id: uuid.UUID, session: AsyncSessionDep) -> DiagnosisReportResponse:
    svc = DiagnosisService(session)
    report = await svc.create_or_get_report(requirement_id)
    return DiagnosisReportResponse.model_validate(report)


@router.get("/{requirement_id}/messages")
async def list_messages(requirement_id: uuid.UUID, session: AsyncSessionDep) -> list[dict]:
    svc = DiagnosisService(session)
    report = await svc.get_report(requirement_id)
    if not report:
        return []
    messages = await svc.list_messages(report.id)
    return [
        {
            "role": m.role,
            "content": m.content,
            "round_num": m.round_num,
            "created_at": m.created_at.isoformat() if m.created_at else "",
        }
        for m in messages
    ]


@router.patch("/{requirement_id}/risks/{risk_id}", response_model=DiagnosisRiskResponse)
async def update_risk(
    requirement_id: uuid.UUID,
    risk_id: uuid.UUID,
    data: DiagnosisRiskUpdate,
    session: AsyncSessionDep,
) -> DiagnosisRiskResponse:
    svc = DiagnosisService(session)
    risk = await svc.get_risk(risk_id)
    if not risk:
        raise HTTPException(status_code=404, detail="DiagnosisRisk not found")
    risk = await svc.update_risk_status(risk, data)
    return DiagnosisRiskResponse.model_validate(risk)
