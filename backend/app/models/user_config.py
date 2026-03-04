from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.sql import func
from app.database import Base


class UserConfig(Base):
    __tablename__ = "user_configs"

    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String(50), nullable=False)
    api_key_encrypted = Column(String(500), nullable=False)
    generator_model = Column(String(100), nullable=True)
    reviewer_model = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
