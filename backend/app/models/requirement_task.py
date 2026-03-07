from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class RequirementTask(Base):
    __tablename__ = "requirement_tasks"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    business_domain = Column(String(100), nullable=True)
    source_type = Column(String(50), nullable=False)
    current_stage = Column(String(50), nullable=False, default="intake")
    task_status = Column(String(50), nullable=False, default="created")
    input_summary = Column(Text, nullable=True)
    input_quality_score = Column(Float, nullable=True)
    ocr_confidence = Column(Float, nullable=True)
    transcription_confidence = Column(Float, nullable=True)
    coverage_score = Column(Float, nullable=True)
    quality_score = Column(Float, nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    archived_at = Column(DateTime(timezone=True), nullable=True)

    project = relationship("Project")
    source_documents = relationship("SourceDocument", back_populates="task", cascade="all, delete-orphan")
    structured_versions = relationship("StructuredRequirementVersion", back_populates="task", cascade="all, delete-orphan")
    test_point_versions = relationship("TestPointVersion", back_populates="task", cascade="all, delete-orphan")
    case_package_versions = relationship("TestCasePackageVersion", back_populates="task", cascade="all, delete-orphan")
    reviews = relationship("ReviewRecord", back_populates="task", cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="task", cascade="all, delete-orphan")
