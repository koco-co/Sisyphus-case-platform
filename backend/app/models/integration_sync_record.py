from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from app.database import Base


class IntegrationSyncRecord(Base):
    __tablename__ = 'integration_sync_records'

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey('requirement_tasks.id', ondelete='CASCADE'), nullable=False, index=True)
    provider = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False)
    output_path = Column(Text, nullable=True)
    message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
