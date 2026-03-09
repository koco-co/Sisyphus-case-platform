import logging

from sqlalchemy import Text, cast, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.products.models import Requirement
from app.modules.scene_map.models import TestPoint
from app.modules.search.schemas import SearchResultItem
from app.modules.testcases.models import TestCase

logger = logging.getLogger(__name__)

_ENTITY_MODELS = {
    "requirement": (Requirement, Requirement.title),
    "testcase": (TestCase, TestCase.title),
    "test_point": (TestPoint, TestPoint.title),
}

# Table names that have a search_vector generated column
_FTS_TABLES: dict[str, str] = {
    "requirement": "requirements",
    "testcase": "test_cases",
    "test_point": "test_points",
}


class SearchService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def global_search(
        self,
        keyword: str,
        entity_types: list[str] | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[SearchResultItem], int]:
        if not keyword or not keyword.strip():
            return [], 0

        pattern = f"%{keyword.strip()}%"
        targets = entity_types or list(_ENTITY_MODELS.keys())
        all_items: list[SearchResultItem] = []

        for et in targets:
            entry = _ENTITY_MODELS.get(et)
            if not entry:
                continue
            model, title_col = entry

            # Try PostgreSQL full-text search first, fall back to ILIKE
            fts_table = _FTS_TABLES.get(et)
            if fts_table:
                try:
                    ts_query = keyword.strip().replace(" ", " & ")
                    fts_sql = text(
                        f"SELECT id FROM {fts_table} "
                        f"WHERE search_vector @@ to_tsquery('simple', :q) "
                        f"AND deleted_at IS NULL"
                    )
                    fts_result = await self.session.execute(fts_sql, {"q": ts_query})
                    fts_ids = {row[0] for row in fts_result.all()}

                    # Also include ILIKE results for partial matches
                    ilike_q = select(model.id).where(
                        cast(title_col, Text).ilike(pattern),
                        model.deleted_at.is_(None),
                    )
                    ilike_result = await self.session.execute(ilike_q)
                    ilike_ids = {row[0] for row in ilike_result.all()}

                    combined_ids = fts_ids | ilike_ids
                    if not combined_ids:
                        continue

                    q = select(model).where(model.id.in_(combined_ids))
                    result = await self.session.execute(q)
                    rows = result.scalars().all()
                except Exception:
                    logger.debug("FTS query failed for %s, falling back to ILIKE", et)
                    q = select(model).where(
                        cast(title_col, Text).ilike(pattern),
                        model.deleted_at.is_(None),
                    )
                    result = await self.session.execute(q)
                    rows = result.scalars().all()
            else:
                q = select(model).where(
                    cast(title_col, Text).ilike(pattern),
                    model.deleted_at.is_(None),
                )
                result = await self.session.execute(q)
                rows = result.scalars().all()

            for row in rows:
                summary = None
                if et == "requirement" and hasattr(row, "req_id"):
                    summary = row.req_id
                elif et == "testcase" and hasattr(row, "case_id"):
                    summary = row.case_id
                elif et == "test_point" and hasattr(row, "description"):
                    summary = (row.description or "")[:120] or None

                all_items.append(
                    SearchResultItem(
                        id=row.id,
                        entity_type=et,
                        title=getattr(row, "title", ""),
                        summary=summary,
                        updated_at=row.updated_at if hasattr(row, "updated_at") else None,
                    )
                )

        all_items.sort(key=lambda x: x.updated_at or x.id, reverse=True)
        total = len(all_items)
        start = (page - 1) * page_size
        return all_items[start : start + page_size], total

    async def semantic_search(
        self,
        query: str,
        top_k: int = 10,
        score_threshold: float = 0.4,
    ) -> list[dict]:
        """Perform semantic search via Qdrant RAG retriever."""
        try:
            from app.engine.rag.retriever import retrieve

            results = await retrieve(query, top_k=top_k, score_threshold=score_threshold)
            return [
                {
                    "content": r.content,
                    "score": round(r.score, 4),
                    "chunk_id": r.chunk_id,
                    "metadata": r.metadata,
                }
                for r in results
            ]
        except Exception:
            logger.warning("Semantic search failed, returning empty", exc_info=True)
            return []
