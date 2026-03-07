from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("requirement_tasks.id", ondelete="CASCADE"), nullable=True, index=True)
    job_type = Column(String(50), nullable=False)
    target_type = Column(String(100), nullable=False)
    target_id = Column(Integer, nullable=False)
    status = Column(String(50), nullable=False)
    progress = Column(Integer, nullable=False, default=0)
    message = Column(Text, nullable=True)
    result_ref = Column(Text, nullable=True)
    error_code = Column(String(100), nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    task = relationship("RequirementTask", back_populates="jobs")
