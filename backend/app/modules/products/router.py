import uuid

from fastapi import APIRouter, status

from app.core.dependencies import AsyncSessionDep
from app.modules.products.schemas import (
    IterationCreate,
    IterationResponse,
    ProductCreate,
    ProductResponse,
    RequirementCreate,
    RequirementResponse,
)
from app.modules.products.service import IterationService, ProductService, RequirementService

router = APIRouter(prefix="/products", tags=["products"])


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
