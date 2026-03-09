import uuid

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base_model import BaseModel


class ParsedDocument(BaseModel):
    __tablename__ = "parsed_documents"

    requirement_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("requirements.id"), index=True, nullable=True
    )
    original_filename: Mapped[str] = mapped_column(String(500))
    file_type: Mapped[str] = mapped_column(String(20))  # docx, pdf, md, txt, image
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    storage_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    content_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_ast: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    parse_status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, parsing, completed, failed
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
