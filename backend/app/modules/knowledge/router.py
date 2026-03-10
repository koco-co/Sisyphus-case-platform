import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status

from app.core.dependencies import AsyncSessionDep
from app.modules.knowledge.models import KnowledgeDocument
from app.modules.knowledge.schemas import (
    KnowledgeDocCreate,
    KnowledgeDocumentDetailResponse,
    KnowledgeDocumentResponse,
    KnowledgeDocUpdate,
    KnowledgeListResponse,
    KnowledgeSearchRequest,
    KnowledgeSearchResultResponse,
)
from app.modules.knowledge.service import KnowledgeService

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


def _serialize_timestamp(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _serialize_document(doc: KnowledgeDocument) -> dict:
    return {
        "id": str(doc.id),
        "file_name": getattr(doc, "file_name", ""),
        "doc_type": getattr(doc, "doc_type", ""),
        "file_size": getattr(doc, "file_size", 0),
        "vector_status": getattr(doc, "vector_status", "pending"),
        "hit_count": getattr(doc, "hit_count", 0),
        "chunk_count": getattr(doc, "chunk_count", 0),
        "tags": list(getattr(doc, "tags", []) or []),
        "uploaded_at": _serialize_timestamp(getattr(doc, "created_at", None)),
        "updated_at": _serialize_timestamp(getattr(doc, "updated_at", None)),
    }


def _serialize_document_detail(doc: KnowledgeDocument) -> dict:
    payload = _serialize_document(doc)
    payload.update(
        {
            "title": getattr(doc, "title", ""),
            "content": getattr(doc, "content", None),
            "content_ast": getattr(doc, "content_ast", None),
            "source": getattr(doc, "source", None),
            "version": getattr(doc, "version", 1),
            "error_message": getattr(doc, "error_message", None),
        }
    )
    return payload


@router.get("/", response_model=KnowledgeListResponse)
async def list_documents(
    session: AsyncSessionDep,
    doc_type: str | None = None,
    vector_status: str | None = None,
    q: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> KnowledgeListResponse:
    svc = KnowledgeService(session)
    docs, total = await svc.list_documents(doc_type, vector_status, q, page, page_size)
    return KnowledgeListResponse(
        items=[KnowledgeDocumentResponse.model_validate(_serialize_document(doc)) for doc in docs],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/upload",
    response_model=KnowledgeDocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    file: Annotated[UploadFile, File(...)],
    session: AsyncSessionDep,
) -> KnowledgeDocumentResponse:
    svc = KnowledgeService(session)
    doc = await svc.upload_document(file)
    return KnowledgeDocumentResponse.model_validate(_serialize_document(doc))


@router.post(
    "/search",
    response_model=list[KnowledgeSearchResultResponse],
)
async def search_documents(
    data: KnowledgeSearchRequest,
    session: AsyncSessionDep,
) -> list[KnowledgeSearchResultResponse]:
    svc = KnowledgeService(session)
    results = await svc.search(
        data.query,
        top_k=data.top_k,
        score_threshold=data.score_threshold,
        doc_id=data.doc_id,
    )
    return [KnowledgeSearchResultResponse.model_validate(item) for item in results]


@router.post("/", response_model=KnowledgeDocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document(data: KnowledgeDocCreate, session: AsyncSessionDep) -> KnowledgeDocumentResponse:
    svc = KnowledgeService(session)
    doc = await svc.create_document(
        title=data.title,
        file_name=data.file_name or data.title,
        doc_type=data.doc_type,
        file_size=data.file_size,
        content=data.content,
        content_ast=data.content_ast,
        tags=data.tags,
        source=data.source,
        vector_status=data.vector_status,
    )
    return KnowledgeDocumentResponse.model_validate(_serialize_document(doc))


@router.post("/{doc_id}/reindex", response_model=KnowledgeDocumentResponse)
async def reindex_document(
    doc_id: uuid.UUID,
    session: AsyncSessionDep,
) -> KnowledgeDocumentResponse:
    svc = KnowledgeService(session)
    doc = await svc.reindex_document(doc_id)
    return KnowledgeDocumentResponse.model_validate(_serialize_document(doc))


@router.get("/{doc_id}", response_model=KnowledgeDocumentDetailResponse)
async def get_document(doc_id: uuid.UUID, session: AsyncSessionDep) -> KnowledgeDocumentDetailResponse:
    svc = KnowledgeService(session)
    doc = await svc.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return KnowledgeDocumentDetailResponse.model_validate(_serialize_document_detail(doc))


@router.patch("/{doc_id}", response_model=KnowledgeDocumentDetailResponse)
async def update_document(
    doc_id: uuid.UUID,
    data: KnowledgeDocUpdate,
    session: AsyncSessionDep,
) -> KnowledgeDocumentDetailResponse:
    svc = KnowledgeService(session)
    doc = await svc.update_document(
        doc_id,
        title=data.title,
        content=data.content,
        content_ast=data.content_ast,
        tags=data.tags,
        vector_status=data.vector_status,
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return KnowledgeDocumentDetailResponse.model_validate(_serialize_document_detail(doc))


@router.delete("/{doc_id}")
async def delete_document(doc_id: uuid.UUID, session: AsyncSessionDep) -> dict:
    svc = KnowledgeService(session)
    success = await svc.soft_delete(doc_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"ok": True}
