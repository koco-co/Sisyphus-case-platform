import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base_model import BaseModel


class SceneMap(BaseModel):
    __tablename__ = "scene_maps"

    requirement_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("requirements.id"), unique=True, index=True
    )
    status: Mapped[str] = mapped_column(String(20), default="draft")
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class TestPoint(BaseModel):
    __tablename__ = "test_points"

    scene_map_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("scene_maps.id"), index=True)
    group_name: Mapped[str] = mapped_column(String(50))
    title: Mapped[str] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    priority: Mapped[str] = mapped_column(String(10), default="P1")
    status: Mapped[str] = mapped_column(String(20), default="ai_generated")
    estimated_cases: Mapped[int] = mapped_column(Integer, default=3)
    source: Mapped[str] = mapped_column(String(20), default="ai")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
