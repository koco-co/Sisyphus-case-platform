import uuid

from fastapi import APIRouter
from fastapi.responses import Response

from app.core.dependencies import AsyncSessionDep
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
