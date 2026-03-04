from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.models.test_case import TestCase

router = APIRouter(prefix="/api/cases", tags=["cases"])


class TestCaseCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    project_id: int
    module: Optional[str] = Field(None, max_length=255)
    title: str = Field(..., min_length=1, max_length=500)
    prerequisites: Optional[str] = Field(None, max_length=2000)
    steps: str = Field(..., max_length=5000)
    expected_results: str = Field(..., max_length=5000)
    keywords: Optional[str] = Field(None, max_length=500)
    priority: str = "2"
    case_type: str = "功能测试"
    stage: str = "功能测试阶段"


class TestCaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    module: Optional[str]
    title: str
    prerequisites: Optional[str]
    steps: str
    expected_results: str
    keywords: Optional[str]
    priority: str
    case_type: str
    stage: str
    status: str
    created_at: datetime


@router.post("/", response_model=TestCaseResponse, status_code=201)
async def create_test_case(
    case: TestCaseCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建测试用例"""
    db_case = TestCase(**case.model_dump())
    db.add(db_case)
    await db.commit()
    await db.refresh(db_case)
    return db_case


@router.get("/", response_model=list[TestCaseResponse])
async def list_test_cases(
    skip: int = 0,
    limit: int = 100,
    project_id: Optional[int] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """获取测试用例列表"""
    query = select(TestCase)
    if project_id:
        query = query.where(TestCase.project_id == project_id)
    if status:
        query = query.where(TestCase.status == status)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    cases = result.scalars().all()
    return cases


@router.get("/{case_id}", response_model=TestCaseResponse)
async def get_test_case(
    case_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取测试用例详情"""
    result = await db.execute(
        select(TestCase).where(TestCase.id == case_id)
    )
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="测试用例不存在")
    return case


@router.put("/{case_id}", response_model=TestCaseResponse)
async def update_test_case(
    case_id: int,
    case_update: TestCaseCreate,
    db: AsyncSession = Depends(get_db)
):
    """更新测试用例"""
    result = await db.execute(
        select(TestCase).where(TestCase.id == case_id)
    )
    db_case = result.scalar_one_or_none()
    if not db_case:
        raise HTTPException(status_code=404, detail="测试用例不存在")

    for key, value in case_update.model_dump().items():
        setattr(db_case, key, value)

    await db.commit()
    await db.refresh(db_case)
    return db_case


@router.patch("/{case_id}/status")
async def update_case_status(
    case_id: int,
    status: str,
    db: AsyncSession = Depends(get_db)
):
    """更新测试用例状态（审批通过/拒绝）"""
    result = await db.execute(
        select(TestCase).where(TestCase.id == case_id)
    )
    db_case = result.scalar_one_or_none()
    if not db_case:
        raise HTTPException(status_code=404, detail="测试用例不存在")

    if status not in ["pending", "approved", "rejected"]:
        raise HTTPException(status_code=400, detail="无效的状态值")

    db_case.status = status
    await db.commit()
    return {"message": f"测试用例状态已更新为 {status}"}
