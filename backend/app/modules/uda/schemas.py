import uuid

from app.shared.base_schema import BaseResponse, BaseSchema


class ParsedDocumentResponse(BaseResponse):
    requirement_id: uuid.UUID | None
    original_filename: str
    file_type: str
    file_size: int
    content_text: str | None
    content_ast: dict | None
    parse_status: str
    error_message: str | None


class ParseRequest(BaseSchema):
    requirement_id: uuid.UUID | None = None
    title: str | None = None
