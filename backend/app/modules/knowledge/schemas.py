import uuid

from pydantic import BaseModel, Field


class KnowledgeDocumentResponse(BaseModel):
    id: uuid.UUID
    file_name: str
    doc_type: str
    file_size: int
    vector_status: str
    hit_count: int
    chunk_count: int
    tags: list[str] = Field(default_factory=list)
    uploaded_at: str = ""
    updated_at: str = ""


class KnowledgeDocumentDetailResponse(KnowledgeDocumentResponse):
    title: str
    content: str | None = None
    content_ast: dict | None = None
    source: str | None = None
    version: int
    error_message: str | None = None


class KnowledgeListResponse(BaseModel):
    items: list[KnowledgeDocumentResponse]
    total: int
    page: int
    page_size: int


class KnowledgeDocCreate(BaseModel):
    title: str
    file_name: str | None = None
    doc_type: str = "md"
    file_size: int = 0
    content: str | None = None
    content_ast: dict | None = None
    tags: list[str] = Field(default_factory=list)
    source: str | None = None
    vector_status: str = "pending"


class KnowledgeDocUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    content_ast: dict | None = None
    tags: list[str] | None = None
    vector_status: str | None = None


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)
    score_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    doc_id: uuid.UUID | None = None


class KnowledgeSearchResultResponse(BaseModel):
    id: str
    content: str
    score: float
    source_doc: str
    chunk_index: int
