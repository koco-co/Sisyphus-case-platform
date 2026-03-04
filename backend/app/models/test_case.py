from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship, mapped_column
from sqlalchemy.sql import func
from typing import Optional, List
from app.database import Base

# Import Vector type from pgvector
try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    # Fallback for testing environments without pgvector
    Vector = JSON


class TestCase(Base):
    __tablename__ = "test_cases"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    module = Column(String(255), nullable=True)
    title = Column(String(500), nullable=False)
    prerequisites = Column(Text, nullable=True)
    steps = Column(Text, nullable=False)
    expected_results = Column(Text, nullable=False)
    keywords = Column(Text, nullable=True)
    priority = Column(String(50), default="2")
    case_type = Column(String(50), default="功能测试")
    stage = Column(String(50), default="功能测试阶段")
    status = Column(String(50), default="pending")
    # Use VECTOR(384) type from pgvector, with JSON fallback for SQLite
    if Vector != JSON:
        embedding = mapped_column(Vector(384), nullable=True)
    else:
        embedding = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    project = relationship("Project", back_populates="test_cases")
