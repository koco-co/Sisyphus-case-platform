import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base_model import BaseModel


class AnalyticsSnapshot(BaseModel):
    __tablename__ = "analytics_snapshots"
    __table_args__ = (UniqueConstraint("iteration_id", "snapshot_date", name="uq_snapshot_iteration_date"),)

    iteration_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("iterations.id"), index=True)
    snapshot_date: Mapped[date] = mapped_column(Date, index=True)
    metrics: Mapped[dict] = mapped_column(JSONB, default=dict)
    trends: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
