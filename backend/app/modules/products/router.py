import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, File, Form, UploadFile, status

from app.core.dependencies import AsyncSessionDep
from app.modules.products.schemas import (
    IterationCreate,
    IterationResponse,
    IterationUpdate,
    ProductCreate,
    ProductResponse,
    ProductUpdate,
    RequirementCreate,
    RequirementResponse,
    RequirementUpdate,
)
from app.modules.products.service import IterationService, ProductService, RequirementService

router = APIRouter(prefix="/products", tags=["products"])


# ── Product endpoints ──────────────────────────────────────────────


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(data: ProductCreate, session: AsyncSessionDep) -> ProductResponse:
    service = ProductService(session)
    product = await service.create_product(data)
    return ProductResponse.model_validate(product)


@router.get("", response_model=list[ProductResponse])
async def list_products(session: AsyncSessionDep) -> list[ProductResponse]:
    service = ProductService(session)
    products = await service.list_products()
    return [ProductResponse.model_validate(p) for p in products]


@router.patch("/{product_id}", response_model=ProductResponse)
async def update_product(product_id: uuid.UUID, data: ProductUpdate, session: AsyncSessionDep) -> ProductResponse:
    service = ProductService(session)
    product = await service.update_product(product_id, data)
    return ProductResponse.model_validate(product)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(product_id: uuid.UUID, session: AsyncSessionDep) -> None:
    service = ProductService(session)
    await service.soft_delete_product(product_id)


# ── Iteration endpoints ────────────────────────────────────────────


@router.post("/{product_id}/iterations", response_model=IterationResponse, status_code=status.HTTP_201_CREATED)
async def create_iteration(product_id: uuid.UUID, data: IterationCreate, session: AsyncSessionDep) -> IterationResponse:
    data.product_id = product_id
    service = IterationService(session)
    iteration = await service.create_iteration(data)
    return IterationResponse.model_validate(iteration)


@router.get("/{product_id}/iterations", response_model=list[IterationResponse])
async def list_iterations(product_id: uuid.UUID, session: AsyncSessionDep) -> list[IterationResponse]:
    service = IterationService(session)
    iterations = await service.list_by_product(product_id)
    return [IterationResponse.model_validate(i) for i in iterations]


@router.patch("/iterations/{iteration_id}", response_model=IterationResponse)
async def update_iteration(
    iteration_id: uuid.UUID, data: IterationUpdate, session: AsyncSessionDep
) -> IterationResponse:
    service = IterationService(session)
    iteration = await service.update_iteration(iteration_id, data)
    return IterationResponse.model_validate(iteration)


@router.delete("/iterations/{iteration_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_iteration(iteration_id: uuid.UUID, session: AsyncSessionDep) -> None:
    service = IterationService(session)
    await service.soft_delete_iteration(iteration_id)


# ── Requirement endpoints ──────────────────────────────────────────


@router.post(
    "/{product_id}/iterations/{iteration_id}/requirements",
    response_model=RequirementResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_requirement(
    iteration_id: uuid.UUID, data: RequirementCreate, session: AsyncSessionDep
) -> RequirementResponse:
    data.iteration_id = iteration_id
    service = RequirementService(session)
    req = await service.create_requirement(data)
    return RequirementResponse.model_validate(req)


@router.get("/{product_id}/iterations/{iteration_id}/requirements", response_model=list[RequirementResponse])
async def list_requirements(iteration_id: uuid.UUID, session: AsyncSessionDep) -> list[RequirementResponse]:
    service = RequirementService(session)
    reqs = await service.list_by_iteration(iteration_id)
    return [RequirementResponse.model_validate(r) for r in reqs]


@router.get("/{product_id}/requirements", response_model=list[RequirementResponse])
async def list_product_requirements(product_id: uuid.UUID, session: AsyncSessionDep) -> list[RequirementResponse]:
    service = RequirementService(session)
    reqs = await service.list_by_product(product_id)
    return [RequirementResponse.model_validate(r) for r in reqs]


@router.get("/requirements", response_model=list[RequirementResponse])
async def list_all_requirements(session: AsyncSessionDep) -> list[RequirementResponse]:
    service = RequirementService(session)
    reqs = await service.list_all()
    return [RequirementResponse.model_validate(r) for r in reqs]


@router.patch("/requirements/{requirement_id}", response_model=RequirementResponse)
async def update_requirement(
    requirement_id: uuid.UUID, data: RequirementUpdate, session: AsyncSessionDep
) -> RequirementResponse:
    service = RequirementService(session)
    req = await service.update_requirement(requirement_id, data)
    return RequirementResponse.model_validate(req)


@router.delete("/requirements/{requirement_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_requirement(requirement_id: uuid.UUID, session: AsyncSessionDep) -> None:
    service = RequirementService(session)
    await service.soft_delete_requirement(requirement_id)


@router.post("/upload-requirement", response_model=RequirementResponse, status_code=status.HTTP_201_CREATED)
async def upload_requirement(
    file: Annotated[UploadFile, File(...)],
    title: Annotated[str, Form(...)],
    iteration_id: Annotated[uuid.UUID, Form(...)],
    session: AsyncSessionDep = ...,
) -> RequirementResponse:
    """Upload a requirement document (docx, pdf, md, txt) and create a Requirement."""
    from app.modules.uda.parsers import parse_document as uda_parse

    raw_bytes = await file.read()
    filename = file.filename or "unknown.txt"

    try:
        full_text, content_ast = uda_parse(filename, raw_bytes)
    except Exception:
        # Fallback: try to read as text
        full_text = raw_bytes.decode("utf-8", errors="replace")
        sections: list[dict[str, str]] = []
        current_heading = ""
        current_body: list[str] = []
        for line in full_text.splitlines():
            if line.startswith("#"):
                if current_heading or current_body:
                    sections.append({"heading": current_heading, "body": "\n".join(current_body).strip()})
                current_heading = line.lstrip("#").strip()
                current_body = []
            else:
                current_body.append(line)
        if current_heading or current_body:
            sections.append({"heading": current_heading, "body": "\n".join(current_body).strip()})
        content_ast = {"raw_text": full_text, "sections": sections}

    req_id = f"REQ-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    data = RequirementCreate(
        iteration_id=iteration_id,
        req_id=req_id,
        title=title,
        content_ast=content_ast,
    )
    service = RequirementService(session)
    req = await service.create_requirement(data)
    return RequirementResponse.model_validate(req)


@router.post(
    "/requirements/{requirement_id}/paste-image",
    response_model=RequirementResponse,
)
async def paste_image_to_requirement(
    requirement_id: uuid.UUID,
    file: Annotated[UploadFile, File(...)],
    session: AsyncSessionDep,
) -> RequirementResponse:
    """Handle image paste upload: parse via UDA and append to requirement content_ast."""
    from app.modules.uda.parsers import parse_document as uda_parse

    raw_bytes = await file.read()
    filename = file.filename or "pasted_image.png"

    _full_text, parsed_ast = uda_parse(filename, raw_bytes)

    service = RequirementService(session)
    req = await service.append_parsed_content(requirement_id, filename, parsed_ast)
    return RequirementResponse.model_validate(req)
