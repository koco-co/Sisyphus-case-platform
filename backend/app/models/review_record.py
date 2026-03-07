from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class ReviewRecord(Base):
    __tablename__ = "review_records"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("requirement_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    target_type = Column(String(100), nullable=False)
    target_version_id = Column(Integer, nullable=False)
    stage = Column(String(50), nullable=False)
    reviewer_id = Column(Integer, nullable=True)
    review_result = Column(String(50), nullable=False)
    review_comment = Column(Text, nullable=True)
    review_tags = Column(Text, nullable=True)
    rollback_to_stage = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    task = relationship("RequirementTask", back_populates="reviews")
