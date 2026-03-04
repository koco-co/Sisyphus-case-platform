"""向量管理 API"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field
from typing import List, Optional

from app.database import get_db
from app.models.test_case import TestCase
from app.rag.retriever import VectorRetriever

router = APIRouter(prefix="/api/vectors", tags=["vectors"])


class SearchRequest(BaseModel):
    """向量检索请求"""
    query: str = Field(..., min_length=1, description="查询文本")
    top_k: int = Field(5, ge=1, le=20, description="返回结果数量")
    status: str = Field("approved", description="用例状态过滤")
    project_id: Optional[int] = Field(None, description="项目 ID 过滤")
    min_similarity: float = Field(0.5, ge=0.0, le=1.0, description="最小相似度阈值")


class SearchResult(BaseModel):
    """向量检索结果"""
    id: int
    title: str
    similarity: float
    steps: str
    expected_results: str
    module: Optional[str] = None
    priority: str = "2"
    case_type: str = "功能测试"


class BatchIndexRequest(BaseModel):
    """批量索引请求"""
    case_ids: List[int] = Field(..., min_length=1, description="测试用例 ID 列表")


@router.post("/cases/{case_id}/index")
async def index_test_case(
    case_id: int,
    db: AsyncSession = Depends(get_db)
):
    """为测试用例创建向量索引"""
    result = await db.execute(
        select(TestCase).where(TestCase.id == case_id)
    )
    case = result.scalar_one_or_none()

    if not case:
        raise HTTPException(status_code=404, detail="测试用例不存在")

    retriever = VectorRetriever()
    await retriever.index_test_case(case, db=db)

    return {"message": "向量索引创建成功", "case_id": case_id}


@router.post("/cases/batch-index")
async def batch_index_test_cases(
    request: BatchIndexRequest,
    db: AsyncSession = Depends(get_db)
):
    """批量创建向量索引"""
    result = await db.execute(
        select(TestCase).where(TestCase.id.in_(request.case_ids))
    )
    cases = result.scalars().all()

    if not cases:
        raise HTTPException(status_code=404, detail="没有找到测试用例")

    retriever = VectorRetriever()
    await retriever.index_batch(cases, db=db)

    return {
        "message": f"已为 {len(cases)} 条测试用例创建索引",
        "count": len(cases)
    }


@router.post("/search", response_model=List[SearchResult])
async def search_similar_cases(
    request: SearchRequest,
    db: AsyncSession = Depends(get_db)
):
    """检索相似的测试用例（基于向量相似度）"""
    retriever = VectorRetriever()

    cases = await retriever.search_similar_cases(
        query=request.query,
        top_k=request.top_k,
        status=request.status,
        project_id=request.project_id,
        min_similarity=request.min_similarity,
        db=db
    )

    return [
        SearchResult(
            id=case.id,
            title=case.title,
            similarity=getattr(case, 'similarity', 0.0),
            steps=case.steps,
            expected_results=case.expected_results,
            module=case.module,
            priority=case.priority,
            case_type=case.case_type
        )
        for case in cases
    ]
