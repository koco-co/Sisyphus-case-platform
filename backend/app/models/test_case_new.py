from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

if TYPE_CHECKING:
    from app.models.requirement import Requirement


class TestCaseNew(Base):
    __tablename__ = "test_cases_new"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    requirement_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("requirements.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    priority: Mapped[str] = mapped_column(String(10), default="P2")
    preconditions: Mapped[Optional[str]] = mapped_column(Text)
    steps: Mapped[list] = mapped_column(JSONB, default=list)
    tags: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    requirement: Mapped["Requirement"] = relationship("Requirement", back_populates="test_cases")
