"""测试用例 API (新版)"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.models.test_case_new import TestCaseNew

router = APIRouter(prefix="/api/testcases", tags=["testcases"])


# Schemas
class TestStep(BaseModel):
    step: int
    action: str
    expected: str


class TestCaseResponse(BaseModel):
    id: str
    requirement_id: str
    title: str
    priority: str
    preconditions: Optional[str]
    steps: list[TestStep]
    tags: list[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TestCaseBrief(BaseModel):
    id: str
    title: str
    priority: str

    class Config:
        from_attributes = True


# Endpoints
@router.get("/{testcase_id}", response_model=TestCaseResponse)
async def get_testcase(
    testcase_id: str,
    db: AsyncSession = Depends(get_db),
):
    """获取测试用例详情"""
    result = await db.execute(
        select(TestCaseNew).where(TestCaseNew.id == testcase_id)
    )
    testcase = result.scalar_one_or_none()

    if not testcase:
        raise HTTPException(status_code=404, detail="测试用例不存在")

    return testcase


@router.get("/requirement/{requirement_id}", response_model=list[TestCaseBrief])
async def list_testcases_by_requirement(
    requirement_id: str,
    db: AsyncSession = Depends(get_db),
):
    """获取需求关联的测试用例列表"""
    result = await db.execute(
        select(TestCaseNew)
        .where(TestCaseNew.requirement_id == requirement_id)
        .order_by(TestCaseNew.priority, TestCaseNew.created_at.desc())
    )
    testcases = result.scalars().all()

    return [TestCaseBrief.model_validate(tc) for tc in testcases]
