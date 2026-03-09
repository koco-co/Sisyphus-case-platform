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
    stream = await svc.run_stream(requirement_id)
    return StreamingResponse(stream, media_type="text/event-stream")


@router.post("/{requirement_id}/chat")
async def chat_diagnosis(
    requirement_id: uuid.UUID,
    data: ChatRequest,
    session: AsyncSessionDep,
) -> StreamingResponse:
    svc = DiagnosisService(session)
    stream = await svc.chat_stream(requirement_id, data.message)
    return StreamingResponse(stream, media_type="text/event-stream")


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
