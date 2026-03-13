import uuid

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base_model import BaseModel


class TestCaseFolder(BaseModel):
    """Hierarchical folder structure for test cases (max 3 levels)."""

    __tablename__ = "test_case_folders"

    name: Mapped[str] = mapped_column(String(200))
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("test_case_folders.id"),
        nullable=True,
        index=True,
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    level: Mapped[int] = mapped_column(Integer, default=1)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)


class TestCase(BaseModel):
    __tablename__ = "test_cases"

    requirement_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("requirements.id"), nullable=True, index=True
    )
    scene_node_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    generation_session_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    case_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    title: Mapped[str] = mapped_column(Text)
    module_path: Mapped[str | None] = mapped_column(String(200), nullable=True)
    precondition: Mapped[str | None] = mapped_column(Text, nullable=True)
    priority: Mapped[str] = mapped_column(String(10), default="P1")
    case_type: Mapped[str] = mapped_column(String(20), default="functional")
    status: Mapped[str] = mapped_column(String(20), default="draft")
    source: Mapped[str] = mapped_column(String(20), default="ai_generated")
    steps: Mapped[list] = mapped_column(JSONB, default=list)
    tags: Mapped[list] = mapped_column(JSONB, default=list)
    ai_score: Mapped[float | None] = mapped_column(nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    reviewer_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    review_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)

    # Data cleaning fields
    clean_status: Mapped[str] = mapped_column(String(20), default="raw")
    quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    original_raw: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # v2.0: folder support
    folder_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("test_case_folders.id"),
        nullable=True,
        index=True,
    )


class TestCaseStep(BaseModel):
    __tablename__ = "test_case_steps"

    test_case_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("test_cases.id"), index=True)
    step_num: Mapped[int] = mapped_column(Integer)
    action: Mapped[str] = mapped_column(Text)
    expected_result: Mapped[str] = mapped_column(Text)


class TestCaseVersion(BaseModel):
    __tablename__ = "test_case_versions"

    test_case_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("test_cases.id"), index=True)
    version: Mapped[int] = mapped_column(Integer)
    snapshot: Mapped[dict] = mapped_column(JSONB)
    change_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
