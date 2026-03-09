import uuid

from fastapi import APIRouter, status
from fastapi.responses import Response

from app.core.dependencies import AsyncSessionDep
from app.modules.export.schemas import (
    ExportJobCreate,
    ExportJobResponse,
    ExportJobStatusResponse,
    JiraPushRequest,
    JiraPushResponse,
)
from app.modules.export.service import ExportService

router = APIRouter(prefix="/export", tags=["export"])


@router.get("/json")
async def export_json(session: AsyncSessionDep, requirement_id: uuid.UUID | None = None) -> Response:
    svc = ExportService(session)
    content = await svc.export_cases_json(requirement_id)
    return Response(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=test_cases.json"},
    )


@router.get("/csv")
async def export_csv(session: AsyncSessionDep, requirement_id: uuid.UUID | None = None) -> Response:
    svc = ExportService(session)
    content = await svc.export_cases_csv(requirement_id)
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=test_cases.csv"},
    )


@router.post("", response_model=ExportJobResponse, status_code=status.HTTP_201_CREATED)
async def create_export_job(session: AsyncSessionDep, params: ExportJobCreate) -> ExportJobResponse:
    svc = ExportService(session)
    job = await svc.create_export_job(params)
    return ExportJobResponse.model_validate(job)


@router.get("/{job_id}", response_model=ExportJobStatusResponse)
async def get_export_job_status(session: AsyncSessionDep, job_id: uuid.UUID) -> ExportJobStatusResponse:
    svc = ExportService(session)
    job = await svc.get_export_job(job_id)
    if not job:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Export job not found")
    return ExportJobStatusResponse.model_validate(job)


@router.get("/{job_id}/download")
async def get_download_url(session: AsyncSessionDep, job_id: uuid.UUID) -> dict[str, str]:
    svc = ExportService(session)
    url = await svc.get_download_url(job_id)
    return {"download_url": url}


@router.post("/{job_id}/generate-word", response_model=ExportJobStatusResponse)
async def generate_word(session: AsyncSessionDep, job_id: uuid.UUID) -> ExportJobStatusResponse:
    svc = ExportService(session)
    job = await svc.generate_word(job_id)
    return ExportJobStatusResponse.model_validate(job)


@router.post("/{job_id}/generate-pdf", response_model=ExportJobStatusResponse)
async def generate_pdf(session: AsyncSessionDep, job_id: uuid.UUID) -> ExportJobStatusResponse:
    svc = ExportService(session)
    job = await svc.generate_pdf(job_id)
    return ExportJobStatusResponse.model_validate(job)


@router.post("/{job_id}/generate-xmind", response_model=ExportJobStatusResponse)
async def generate_xmind(session: AsyncSessionDep, job_id: uuid.UUID) -> ExportJobStatusResponse:
    svc = ExportService(session)
    job = await svc.generate_xmind(job_id)
    return ExportJobStatusResponse.model_validate(job)


@router.post("/{job_id}/generate-markdown", response_model=ExportJobStatusResponse)
async def generate_markdown(session: AsyncSessionDep, job_id: uuid.UUID) -> ExportJobStatusResponse:
    svc = ExportService(session)
    job = await svc.generate_markdown(job_id)
    return ExportJobStatusResponse.model_validate(job)


# ── Jira/Xray Push (B-M12-08) ────────────────────────────────────


@router.post("/push-jira", response_model=JiraPushResponse)
async def push_to_jira(data: JiraPushRequest, session: AsyncSessionDep) -> JiraPushResponse:
    svc = ExportService(session)
    result = await svc.push_to_jira(data.job_id, data.jira_config)
    return JiraPushResponse(**result)
