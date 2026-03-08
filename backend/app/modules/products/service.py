from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.products.models import Iteration, Product, Requirement
from app.modules.products.schemas import IterationCreate, ProductCreate, RequirementCreate


class ProductService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_product(self, data: ProductCreate) -> Product:
        product = Product(**data.model_dump())
        self.session.add(product)
        await self.session.commit()
        await self.session.refresh(product)
        return product

    async def list_products(self) -> list[Product]:
        result = await self.session.execute(select(Product).where(Product.deleted_at.is_(None)))
        return list(result.scalars().all())

    async def get_product(self, product_id: UUID) -> Product | None:
        return await self.session.get(Product, product_id)


class IterationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_iteration(self, data: IterationCreate) -> Iteration:
        iteration = Iteration(**data.model_dump())
        self.session.add(iteration)
        await self.session.commit()
        await self.session.refresh(iteration)
        return iteration

    async def list_by_product(self, product_id: UUID) -> list[Iteration]:
        result = await self.session.execute(
            select(Iteration).where(
                Iteration.product_id == product_id,
                Iteration.deleted_at.is_(None),
            )
        )
        return list(result.scalars().all())


class RequirementService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_requirement(self, data: RequirementCreate) -> Requirement:
        requirement = Requirement(**data.model_dump(exclude_none=True))
        self.session.add(requirement)
        await self.session.commit()
        await self.session.refresh(requirement)
        return requirement

    async def list_by_iteration(self, iteration_id: UUID) -> list[Requirement]:
        result = await self.session.execute(
            select(Requirement).where(
                Requirement.iteration_id == iteration_id,
                Requirement.deleted_at.is_(None),
            )
        )
        return list(result.scalars().all())
