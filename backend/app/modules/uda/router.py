import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, File, Form, UploadFile, status

from app.core.dependencies import AsyncSessionDep
from app.modules.products.schemas import RequirementCreate
from app.modules.products.service import RequirementService
from app.modules.uda.schemas import ParsedDocumentResponse
from app.modules.uda.service import UdaService

router = APIRouter(prefix="/uda", tags=["uda"])


@router.post("/parse", response_model=ParsedDocumentResponse, status_code=status.HTTP_201_CREATED)
async def parse_document(
    file: Annotated[UploadFile, File(...)],
    requirement_id: Annotated[uuid.UUID | None, Form()] = None,
    session: AsyncSessionDep = ...,
) -> ParsedDocumentResponse:
    """Upload and parse a document (docx, pdf, md, txt, image)."""
    service = UdaService(session)
    doc = await service.parse_upload(file, requirement_id)
    return ParsedDocumentResponse.model_validate(doc)


@router.get("/{doc_id}", response_model=ParsedDocumentResponse)
async def get_parsed_document(doc_id: uuid.UUID, session: AsyncSessionDep) -> ParsedDocumentResponse:
    """Get a parsed document by ID."""
    service = UdaService(session)
    doc = await service.get_document(doc_id)
    return ParsedDocumentResponse.model_validate(doc)


@router.get("/by-requirement/{requirement_id}", response_model=list[ParsedDocumentResponse])
async def list_by_requirement(requirement_id: uuid.UUID, session: AsyncSessionDep) -> list[ParsedDocumentResponse]:
    """List parsed documents for a requirement."""
    service = UdaService(session)
    docs = await service.list_by_requirement(requirement_id)
    return [ParsedDocumentResponse.model_validate(d) for d in docs]


@router.post(
    "/parse-to-requirement",
    status_code=status.HTTP_201_CREATED,
)
async def parse_to_requirement(
    file: Annotated[UploadFile, File(...)],
    title: Annotated[str, Form(...)],
    iteration_id: Annotated[uuid.UUID, Form(...)],
    session: AsyncSessionDep = ...,
) -> dict:
    """Parse a document and create a Requirement from its content."""
    uda_service = UdaService(session)
    doc = await uda_service.parse_upload(file)

    if doc.parse_status != "completed":
        return {
            "success": False,
            "error": doc.error_message or "Parse failed",
            "document_id": str(doc.id),
        }

    req_id = f"REQ-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    req_data = RequirementCreate(
        iteration_id=iteration_id,
        req_id=req_id,
        title=title,
        content_ast=doc.content_ast or {},
    )
    req_service = RequirementService(session)
    requirement = await req_service.create_requirement(req_data)

    # Link document to requirement
    doc.requirement_id = requirement.id
    await session.commit()

    return {
        "success": True,
        "requirement_id": str(requirement.id),
        "document_id": str(doc.id),
        "req_id": requirement.req_id,
        "title": requirement.title,
        "content_text_preview": (doc.content_text or "")[:500],
    }
