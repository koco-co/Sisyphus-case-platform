from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.products.models import (
    Iteration,
    Product,
    Requirement,
    RequirementVersion,
)
from app.modules.products.schemas import (
    IterationCreate,
    IterationUpdate,
    ProductCreate,
    ProductUpdate,
    RequirementCreate,
    RequirementUpdate,
)


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

    async def update_product(self, product_id: UUID, data: ProductUpdate) -> Product:
        product = await self.session.get(Product, product_id)
        if not product or product.deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(product, key, value)
        await self.session.commit()
        await self.session.refresh(product)
        return product

    async def soft_delete_product(self, product_id: UUID) -> None:
        product = await self.session.get(Product, product_id)
        if not product or product.deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        product.deleted_at = datetime.now(UTC)
        await self.session.commit()


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

    async def update_iteration(self, iteration_id: UUID, data: IterationUpdate) -> Iteration:
        iteration = await self.session.get(Iteration, iteration_id)
        if not iteration or iteration.deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Iteration not found")
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(iteration, key, value)
        await self.session.commit()
        await self.session.refresh(iteration)
        return iteration

    async def soft_delete_iteration(self, iteration_id: UUID) -> None:
        iteration = await self.session.get(Iteration, iteration_id)
        if not iteration or iteration.deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Iteration not found")
        iteration.deleted_at = datetime.now(UTC)
        await self.session.commit()


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

    async def list_by_product(self, product_id: UUID) -> list[Requirement]:
        result = await self.session.execute(
            select(Requirement)
            .join(Iteration, Requirement.iteration_id == Iteration.id)
            .where(
                Iteration.product_id == product_id,
                Requirement.deleted_at.is_(None),
            )
        )
        return list(result.scalars().all())

    async def list_all(self) -> list[Requirement]:
        result = await self.session.execute(select(Requirement).where(Requirement.deleted_at.is_(None)))
        return list(result.scalars().all())

    async def update_requirement(self, requirement_id: UUID, data: RequirementUpdate) -> Requirement:
        requirement = await self.session.get(Requirement, requirement_id)
        if not requirement or requirement.deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Requirement not found")

        updates = data.model_dump(exclude_unset=True)
        if not updates:
            return requirement

        # Auto-version: snapshot current state before applying changes
        version_snapshot = RequirementVersion(
            requirement_id=requirement.id,
            version=requirement.version,
            content_ast=requirement.content_ast or {},
            change_summary=f"Version {requirement.version} snapshot before update",
        )
        self.session.add(version_snapshot)

        for key, value in updates.items():
            setattr(requirement, key, value)
        requirement.version += 1

        await self.session.commit()
        await self.session.refresh(requirement)
        return requirement

    async def soft_delete_requirement(self, requirement_id: UUID) -> None:
        requirement = await self.session.get(Requirement, requirement_id)
        if not requirement or requirement.deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Requirement not found")
        requirement.deleted_at = datetime.now(UTC)
        await self.session.commit()
