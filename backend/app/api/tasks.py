import os
import tempfile

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.domain.intake.jobs import run_ingestion_job
from app.models.project import Project
from app.models.requirement_task import RequirementTask
from app.models.source_document import SourceDocument
from app.schemas.task import TaskCreate, TaskDocumentResponse, TaskIngestionResponse, TaskResponse

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

_parser_manager = None


def get_parser_manager():
    global _parser_manager
    if _parser_manager is None:
        try:
            from app.plugins.manager import ParserManager

            _parser_manager = ParserManager()
        except ImportError:
            _parser_manager = None
    return _parser_manager


@router.post("", response_model=TaskResponse, status_code=201)
async def create_task(task: TaskCreate, db: AsyncSession = Depends(get_db)):
    project = await db.scalar(select(Project).where(Project.id == task.project_id))
    if project is None:
        raise HTTPException(status_code=404, detail="项目不存在")

    db_task = RequirementTask(
        project_id=task.project_id,
        title=task.title,
        source_type=task.source_type,
        business_domain=task.business_domain,
        input_summary=task.input_summary,
        current_stage="intake",
        task_status="created",
    )
    db.add(db_task)
    await db.commit()
    await db.refresh(db_task)
    return db_task


@router.post("/{task_id}/documents", response_model=TaskDocumentResponse, status_code=201)
async def upload_task_document(
    task_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    task = await db.scalar(select(RequirementTask).where(RequirementTask.id == task_id))
    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在")

    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")

    ext = os.path.splitext(file.filename)[1].lower()
    allowed_extensions = {".md", ".txt", ".pdf", ".doc", ".docx", ".png", ".jpg", ".jpeg"}
    if ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型: {ext}")

    content = await file.read()
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as stored_file:
        stored_file.write(content)
        storage_path = stored_file.name

    extracted_text = None
    parser_manager = get_parser_manager()
    if parser_manager:
        parser = parser_manager.get_parser(f"test{ext}")
        if parser:
            extracted_text = parser.parse(storage_path)

    document = SourceDocument(
        task_id=task.id,
        file_name=file.filename,
        file_type=file.content_type or "application/octet-stream",
        storage_path=storage_path,
        extracted_text=extracted_text,
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)
    return document


@router.post("/{task_id}/ingestion:run", response_model=TaskIngestionResponse, status_code=202)
async def trigger_ingestion(task_id: int, db: AsyncSession = Depends(get_db)):
    task = await run_ingestion_job(db, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在")

    return TaskIngestionResponse(
        task_id=task.id,
        task_status=task.task_status,
        current_stage=task.current_stage,
        input_summary=task.input_summary,
    )
