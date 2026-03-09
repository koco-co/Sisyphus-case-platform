import uuid

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base_model import BaseModel


class DiagnosisReport(BaseModel):
    __tablename__ = "diagnosis_reports"

    requirement_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("requirements.id"), index=True
    )
    status: Mapped[str] = mapped_column(String(20), default="running")
    overall_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    risk_count_high: Mapped[int] = mapped_column(Integer, default=0)
    risk_count_medium: Mapped[int] = mapped_column(Integer, default=0)
    risk_count_industry: Mapped[int] = mapped_column(Integer, default=0)


class DiagnosisRisk(BaseModel):
    __tablename__ = "diagnosis_risks"

    report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("diagnosis_reports.id"), index=True
    )
    level: Mapped[str] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    risk_status: Mapped[str] = mapped_column(String(20), default="pending")


class DiagnosisChatMessage(BaseModel):
    __tablename__ = "diagnosis_chat_messages"

    report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("diagnosis_reports.id"), index=True
    )
    role: Mapped[str] = mapped_column(String(10))
    content: Mapped[str] = mapped_column(Text)
    round_num: Mapped[int] = mapped_column(Integer, default=1)
