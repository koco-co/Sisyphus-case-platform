from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class StructuredRequirementVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    version_no: int
    status: str
    content_json: dict[str, Any]
    created_at: datetime
