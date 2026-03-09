import logging
from uuid import UUID

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.uda.models import ParsedDocument
from app.modules.uda.parsers import parse_document

logger = logging.getLogger(__name__)


class UdaService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def parse_upload(
        self,
        file: UploadFile,
        requirement_id: UUID | None = None,
    ) -> ParsedDocument:
        raw_bytes = await file.read()
        filename = file.filename or "unknown"
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "txt"

        doc = ParsedDocument(
            requirement_id=requirement_id,
            original_filename=filename,
            file_type=ext,
            file_size=len(raw_bytes),
            parse_status="parsing",
        )
        self.session.add(doc)
        await self.session.flush()

        try:
            full_text, content_ast = parse_document(filename, raw_bytes)
            doc.content_text = full_text
            doc.content_ast = content_ast
            doc.parse_status = "completed"
        except Exception as e:
            logger.exception("Failed to parse document: %s", filename)
            doc.parse_status = "failed"
            doc.error_message = str(e)

        await self.session.commit()
        await self.session.refresh(doc)
        return doc

    async def get_document(self, doc_id: UUID) -> ParsedDocument:
        doc = await self.session.get(ParsedDocument, doc_id)
        if not doc or doc.deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        return doc

    async def list_by_requirement(self, requirement_id: UUID) -> list[ParsedDocument]:
        result = await self.session.execute(
            select(ParsedDocument).where(
                ParsedDocument.requirement_id == requirement_id,
                ParsedDocument.deleted_at.is_(None),
            )
        )
        return list(result.scalars().all())
