from fastapi import APIRouter, Query

from app.core.dependencies import AsyncSessionDep
from app.modules.search.schemas import SearchResponse
from app.modules.search.service import SearchService

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=SearchResponse)
async def global_search(
    session: AsyncSessionDep,
    q: str = Query("", min_length=1, description="搜索关键词"),
    types: str | None = Query(None, description="实体类型，逗号分隔: requirement,testcase,test_point"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> dict:
    entity_types = [t.strip() for t in types.split(",") if t.strip()] if types else None
    svc = SearchService(session)
    items, total = await svc.global_search(q, entity_types, page, page_size)
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/semantic")
async def semantic_search(
    session: AsyncSessionDep,
    q: str = Query(..., min_length=1, description="语义查询"),
    top_k: int = Query(10, ge=1, le=50),
    score_threshold: float = Query(0.4, ge=0.0, le=1.0),
) -> dict:
    """Semantic search powered by Qdrant vector retrieval."""
    svc = SearchService(session)
    results = await svc.semantic_search(q, top_k, score_threshold)
    return {"query": q, "results": results, "count": len(results)}
