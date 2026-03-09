import uuid

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel as PydanticBaseModel

from app.core.dependencies import AsyncSessionDep
from app.modules.knowledge.service import KnowledgeService

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


class KnowledgeDocCreate(PydanticBaseModel):
    title: str
    doc_type: str = "standard"
    content: str | None = None
    tags: dict | None = None
    source: str | None = None


class KnowledgeDocUpdate(PydanticBaseModel):
    title: str | None = None
    content: str | None = None
    tags: dict | None = None
    status: str | None = None


@router.get("/")
async def list_documents(
    session: AsyncSessionDep,
    doc_type: str | None = None,
    status: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> dict:
    svc = KnowledgeService(session)
    docs, total = await svc.list_documents(doc_type, status, page, page_size)
    return {
        "items": [
            {
                "id": str(d.id),
                "title": d.title,
                "doc_type": d.doc_type,
                "tags": d.tags,
                "source": d.source,
                "version": d.version,
                "status": d.status,
                "created_at": d.created_at.isoformat() if d.created_at else "",
            }
            for d in docs
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{doc_id}")
async def get_document(doc_id: uuid.UUID, session: AsyncSessionDep) -> dict:
    svc = KnowledgeService(session)
    doc = await svc.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return {
        "id": str(doc.id),
        "title": doc.title,
        "doc_type": doc.doc_type,
        "content": doc.content,
        "tags": doc.tags,
        "source": doc.source,
        "version": doc.version,
        "status": doc.status,
        "created_at": doc.created_at.isoformat() if doc.created_at else "",
    }


@router.post("/", status_code=201)
async def create_document(data: KnowledgeDocCreate, session: AsyncSessionDep) -> dict:
    svc = KnowledgeService(session)
    doc = await svc.create_document(
        title=data.title,
        doc_type=data.doc_type,
        content=data.content,
        tags=data.tags,
        source=data.source,
    )
    return {"id": str(doc.id), "title": doc.title}


@router.patch("/{doc_id}")
async def update_document(doc_id: uuid.UUID, data: KnowledgeDocUpdate, session: AsyncSessionDep) -> dict:
    svc = KnowledgeService(session)
    doc = await svc.update_document(
        doc_id,
        title=data.title,
        content=data.content,
        tags=data.tags,
        status=data.status,
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"id": str(doc.id), "version": doc.version}


@router.delete("/{doc_id}")
async def delete_document(doc_id: uuid.UUID, session: AsyncSessionDep) -> dict:
    svc = KnowledgeService(session)
    success = await svc.soft_delete(doc_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"ok": True}


@router.post("/test")
async def test_rag_retrieval(
    session: AsyncSessionDep,
    query: str = Query(..., min_length=1, description="测试查询语句"),
    top_k: int = Query(5, ge=1, le=20),
    score_threshold: float = Query(0.5, ge=0.0, le=1.0),
    doc_id: uuid.UUID | None = None,
) -> dict:
    """Test RAG retrieval hit rate — returns matching chunks with scores."""
    doc_ids = [str(doc_id)] if doc_id else None
    try:
        from app.engine.rag.retriever import retrieve

        results = await retrieve(query, top_k=top_k, score_threshold=score_threshold, doc_ids=doc_ids)
        return {
            "query": query,
            "total_hits": len(results),
            "hits": [
                {
                    "chunk_id": r.chunk_id,
                    "score": round(r.score, 4),
                    "content_preview": r.content[:300],
                    "metadata": r.metadata,
                }
                for r in results
            ],
            "avg_score": round(sum(r.score for r in results) / len(results), 4) if results else 0.0,
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"RAG retrieval failed: {e}") from e
