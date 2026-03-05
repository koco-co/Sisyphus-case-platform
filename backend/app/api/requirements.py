"""需求 API"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

from app.database import get_db
from app.models.requirement import Requirement
from app.models.test_case_new import TestCaseNew

router = APIRouter(prefix="/api/requirements", tags=["requirements"])


# Schemas
class FeatureSchema(BaseModel):
    name: str
    description: Optional[str] = None
    input: Optional[str] = None
    output: Optional[str] = None
    exceptions: Optional[str] = None


class ModuleSchema(BaseModel):
    name: str
    description: Optional[str] = None
    features: list[FeatureSchema] = []


class StructuredContentSchema(BaseModel):
    modules: list[ModuleSchema] = []


class RequirementResponse(BaseModel):
    id: UUID
    project_id: int
    title: str
    content: StructuredContentSchema
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TestCaseBrief(BaseModel):
    id: UUID
    title: str
    priority: str

    class Config:
        from_attributes = True


class RequirementCreate(BaseModel):
    project_id: int
    title: str
    content: Optional[StructuredContentSchema] = None
    source_file_id: Optional[str] = None


# Endpoints
@router.post("/", response_model=RequirementResponse, status_code=201)
async def create_requirement(
    data: RequirementCreate,
    db: AsyncSession = Depends(get_db),
):
    """创建需求"""
    requirement = Requirement(
        project_id=data.project_id,
        title=data.title,
        content=data.content.model_dump() if data.content else {},
        source_file_id=data.source_file_id,
    )
    db.add(requirement)
    await db.commit()
    await db.refresh(requirement)
    return requirement
@router.get("/{requirement_id}", response_model=RequirementResponse)
async def get_requirement(
    requirement_id: str,
    db: AsyncSession = Depends(get_db),
):
    """获取需求详情"""
    result = await db.execute(
        select(Requirement).where(Requirement.id == requirement_id)
    )
    requirement = result.scalar_one_or_none()

    if not requirement:
        raise HTTPException(status_code=404, detail="需求不存在")

    return requirement


@router.get("/{requirement_id}/testcases", response_model=list[TestCaseBrief])
async def get_requirement_testcases(
    requirement_id: str,
    db: AsyncSession = Depends(get_db),
):
    """获取需求关联的测试用例"""
    result = await db.execute(
        select(TestCaseNew)
        .where(TestCaseNew.requirement_id == requirement_id)
        .order_by(TestCaseNew.created_at.desc())
    )
    test_cases = result.scalars().all()

    return [TestCaseBrief.model_validate(tc) for tc in test_cases]
