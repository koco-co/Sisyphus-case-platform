"""M02 历史数据导入清洗 — ORM 模型"""

from __future__ import annotations

import uuid

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.base_model import BaseModel


class ImportJob(BaseModel):
    """导入任务。"""

    __tablename__ = "import_jobs"

    file_name: Mapped[str] = mapped_column(String(500))
    file_type: Mapped[str] = mapped_column(String(20))  # csv / excel / markdown
    status: Mapped[str] = mapped_column(
        String(30), default="pending"
    )  # pending / parsing / mapping / cleaning / reviewing / completed / failed
    total_records: Mapped[int] = mapped_column(Integer, default=0)
    success_count: Mapped[int] = mapped_column(Integer, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, default=0)
    duplicate_count: Mapped[int] = mapped_column(Integer, default=0)
    product_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    health_report: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    field_mapping: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    records: Mapped[list[ImportRecord]] = relationship(back_populates="job", cascade="all, delete-orphan")


class ImportRecord(BaseModel):
    """导入记录（逐条）。"""

    __tablename__ = "import_records"

    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("import_jobs.id"))
    row_number: Mapped[int] = mapped_column(Integer)
    original_title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    mapped_title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    raw_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    mapped_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(
        String(30), default="pending"
    )  # pending / accepted / rejected / merged / duplicate / error / imported
    match_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    duplicate_of: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    job: Mapped[ImportJob] = relationship(back_populates="records")
