from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.sql import func

from app.database import Base


class KnowledgeAsset(Base):
    __tablename__ = 'knowledge_assets'

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey('requirement_tasks.id', ondelete='SET NULL'), nullable=True, index=True)
    asset_type = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    summary = Column(Text, nullable=True)
    content_json = Column(JSON, nullable=False, default=dict)
    status = Column(String(50), nullable=False, default='candidate')
    quality_level = Column(String(50), nullable=False, default='candidate')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
