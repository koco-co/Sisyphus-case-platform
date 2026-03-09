import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base_model import BaseModel


class CoverageMatrix(BaseModel):
    __tablename__ = "coverage_matrices"

    requirement_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("requirements.id"), index=True)
    scene_node_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    test_case_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    coverage_type: Mapped[str] = mapped_column(String(20), default="none")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
