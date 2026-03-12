import uuid

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

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
    collector = await svc.run_and_persist_stream(requirement_id)
    return StreamingResponse(collector, media_type="text/event-stream")


@router.post("/{requirement_id}/chat")
async def chat_diagnosis(
    requirement_id: uuid.UUID,
    data: ChatRequest,
    session: AsyncSessionDep,
) -> StreamingResponse:
    svc = DiagnosisService(session)
    collector = await svc.chat_and_persist_stream(requirement_id, data.message)
    return StreamingResponse(collector, media_type="text/event-stream")


@router.post("/{requirement_id}/create", response_model=DiagnosisReportResponse)
async def create_report(requirement_id: uuid.UUID, session: AsyncSessionDep) -> DiagnosisReportResponse:
    svc = DiagnosisService(session)
    report = await svc.create_or_get_report(requirement_id)
    risks = await svc.list_risks(report.id)
    resp = DiagnosisReportResponse.model_validate(report)
    resp.risks = [DiagnosisRiskResponse.model_validate(r) for r in risks]
    return resp


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
