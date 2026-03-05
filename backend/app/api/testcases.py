"""测试用例 API (新版)"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID

from app.database import get_db
from app.models import TestCaseNew

router = APIRouter(prefix="/api/testcases", tags=["testcases"])


# Schemas
class TestStep(BaseModel):
    step: int
    action: str
    expected: str


class TestCaseCreate(BaseModel):
    """创建测试用例请求"""
    title: str
    priority: str = "P2"
    preconditions: Optional[str] = None
    steps: List[TestStep] = []
    tags: List[str] = []


class TestCaseBatchCreate(BaseModel):
    """批量创建测试用例请求"""
    requirement_id: str
    test_cases: List[TestCaseCreate]


class TestCaseResponse(BaseModel):
    id: str
    requirement_id: str
    title: str
    priority: str
    preconditions: Optional[str]
    steps: List[TestStep]
    tags: List[str]
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


@router.get("/requirement/{requirement_id}", response_model=List[TestCaseBrief])
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


@router.post("/", response_model=List[TestCaseResponse], status_code=201)
async def create_testcases(
    data: TestCaseBatchCreate,
    db: AsyncSession = Depends(get_db),
):
    """批量创建测试用例"""
    try:
        requirement_uuid = UUID(data.requirement_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的需求 ID 格式")

    created_cases = []
    for tc_data in data.test_cases:
        # 转换步骤格式
        steps = [step.model_dump() for step in tc_data.steps]

        testcase = TestCaseNew(
            requirement_id=requirement_uuid,
            title=tc_data.title,
            priority=tc_data.priority,
            preconditions=tc_data.preconditions,
            steps=steps,
            tags=tc_data.tags or [],
        )
        db.add(testcase)
        created_cases.append(testcase)

    await db.commit()

    # Refresh to get generated IDs
    for tc in created_cases:
        await db.refresh(tc)

    return [TestCaseResponse.model_validate(tc) for tc in created_cases]
