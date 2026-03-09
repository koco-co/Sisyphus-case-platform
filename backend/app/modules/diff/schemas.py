import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DiffResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    requirement_id: uuid.UUID
    version_from: int
    version_to: int
    text_diff: dict
    semantic_impact: dict | None = None
    impact_level: str
    affected_test_points: dict | None = None
    affected_test_cases: dict | None = None
    summary: str | None = None
    created_at: datetime | None = None


class DiffRequest(BaseModel):
    version_from: int
    version_to: int


class SuggestionItem(BaseModel):
    name: str
    description: str = ""
    category: str = "normal"
    priority: str = "P1"
    reason: str = ""


class SuggestionResponse(BaseModel):
    suggestions: list[SuggestionItem]
    count: int


class RegenerateRequest(BaseModel):
    test_point_ids: list[str] | None = None


class RegenerateResponse(BaseModel):
    regenerated_cases: list[dict]
    count: int
