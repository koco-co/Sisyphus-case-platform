import uuid

from sqlalchemy import Float, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base_model import BaseModel


class AiConfiguration(BaseModel):
    __tablename__ = "ai_configurations"

    scope: Mapped[str] = mapped_column(String(20), default="global")
    scope_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    system_rules_version: Mapped[str] = mapped_column(String(20), default="1.0")
    team_standard_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    module_rules: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    output_preference: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    scope_preference: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    rag_config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    custom_checklist: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    llm_model: Mapped[str | None] = mapped_column(String(50), nullable=True)
    llm_temperature: Mapped[float | None] = mapped_column(Float, nullable=True)
