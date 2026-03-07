from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TaskCreate(BaseModel):
    project_id: int = Field(..., gt=0)
    title: str = Field(..., min_length=1, max_length=255)
    source_type: str = Field(..., min_length=1, max_length=50)
    business_domain: Optional[str] = Field(None, max_length=100)
    input_summary: Optional[str] = None


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    title: str
    source_type: str
    business_domain: Optional[str]
    current_stage: str
    task_status: str
    input_summary: Optional[str]
    created_at: datetime
    updated_at: datetime


class TaskDocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    file_name: str
    file_type: str
    storage_path: str
    extracted_text: Optional[str]
    quality_score: Optional[float]
    created_at: datetime


class TaskIngestionResponse(BaseModel):
    task_id: int
    task_status: str
    current_stage: str
    input_summary: Optional[str]
