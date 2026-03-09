from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.templates.models import TestCaseTemplate
from app.modules.templates.schemas import TemplateCreate, TemplateUpdate


class TemplateService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_templates(
        self,
        category: str | None = None,
        keyword: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[TestCaseTemplate], int]:
        q = select(TestCaseTemplate).where(TestCaseTemplate.deleted_at.is_(None))
        count_q = select(func.count()).select_from(TestCaseTemplate).where(TestCaseTemplate.deleted_at.is_(None))

        if category:
            q = q.where(TestCaseTemplate.category == category)
            count_q = count_q.where(TestCaseTemplate.category == category)

        if keyword:
            pattern = f"%{keyword}%"
            q = q.where(
                or_(
                    TestCaseTemplate.name.ilike(pattern),
                    TestCaseTemplate.description.ilike(pattern),
                )
            )
            count_q = count_q.where(
                or_(
                    TestCaseTemplate.name.ilike(pattern),
                    TestCaseTemplate.description.ilike(pattern),
                )
            )

        total: int = (await self.session.execute(count_q)).scalar() or 0
        q = q.order_by(TestCaseTemplate.usage_count.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self.session.execute(q)
        return list(result.scalars().all()), total

    async def get_template(self, template_id: UUID) -> TestCaseTemplate:
        tpl = await self.session.get(TestCaseTemplate, template_id)
        if not tpl or tpl.deleted_at is not None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found",
            )
        return tpl

    async def create_template(self, data: TemplateCreate) -> TestCaseTemplate:
        tpl = TestCaseTemplate(**data.model_dump())
        self.session.add(tpl)
        await self.session.commit()
        await self.session.refresh(tpl)
        return tpl

    async def update_template(self, template_id: UUID, data: TemplateUpdate) -> TestCaseTemplate:
        tpl = await self.get_template(template_id)
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(tpl, key, value)
        await self.session.commit()
        await self.session.refresh(tpl)
        return tpl

    async def apply_template(
        self,
        template_id: UUID,
        requirement_id: UUID,
        variables: dict | None = None,
    ) -> dict:
        """Apply a template: substitute variables and return the ready content."""
        tpl = await self.get_template(template_id)

        content = tpl.template_content.copy()
        merged_vars = {**(tpl.variables or {}), **(variables or {})}

        def _substitute(text: str) -> str:
            for k, v in merged_vars.items():
                text = text.replace(f"{{{{{k}}}}}", str(v))
            return text

        if "precondition" in content and isinstance(content["precondition"], str):
            content["precondition"] = _substitute(content["precondition"])

        if "steps" in content and isinstance(content["steps"], list):
            for step in content["steps"]:
                if isinstance(step, dict):
                    for field in ("step", "action", "expected"):
                        if field in step and isinstance(step[field], str):
                            step[field] = _substitute(step[field])

        tpl.usage_count += 1
        await self.session.commit()

        return {
            "template_id": tpl.id,
            "applied_content": content,
        }

    async def soft_delete(self, template_id: UUID) -> None:
        tpl = await self.get_template(template_id)
        tpl.deleted_at = datetime.now(UTC)
        await self.session.commit()
