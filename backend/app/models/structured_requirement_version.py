from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class StructuredRequirementVersion(Base):
    __tablename__ = "structured_requirement_versions"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("requirement_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    version_no = Column(Integer, nullable=False)
    status = Column(String(50), nullable=False)
    content_json = Column(JSON, nullable=False, default=dict)
    source_snapshot_id = Column(Integer, nullable=True)
    generated_by = Column(String(50), nullable=True)
    based_on_version = Column(Integer, nullable=True)
    change_summary = Column(Text, nullable=True)
    created_by = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    task = relationship("RequirementTask", back_populates="structured_versions")
