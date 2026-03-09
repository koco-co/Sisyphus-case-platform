import json
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.prompts import assemble_prompt
from app.ai.stream_adapter import get_thinking_stream
from app.modules.products.models import Requirement
from app.modules.scene_map.models import SceneMap, TestPoint
from app.modules.scene_map.schemas import TestPointCreate, TestPointUpdate


class SceneMapService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_or_create(self, requirement_id: UUID) -> SceneMap:
        q = select(SceneMap).where(
            SceneMap.requirement_id == requirement_id,
            SceneMap.deleted_at.is_(None),
        )
        result = await self.session.execute(q)
        scene_map = result.scalar_one_or_none()
        if scene_map:
            return scene_map

        scene_map = SceneMap(requirement_id=requirement_id, status="draft")
        self.session.add(scene_map)
        await self.session.commit()
        await self.session.refresh(scene_map)
        return scene_map

    async def get_map(self, requirement_id: UUID) -> SceneMap | None:
        q = select(SceneMap).where(
            SceneMap.requirement_id == requirement_id,
            SceneMap.deleted_at.is_(None),
        )
        result = await self.session.execute(q)
        return result.scalar_one_or_none()

    async def list_test_points(self, scene_map_id: UUID) -> list[TestPoint]:
        q = (
            select(TestPoint)
            .where(
                TestPoint.scene_map_id == scene_map_id,
                TestPoint.deleted_at.is_(None),
            )
            .order_by(TestPoint.group_name, TestPoint.created_at)
        )
        result = await self.session.execute(q)
        return list(result.scalars().all())

    async def add_test_point(
        self,
        scene_map_id: UUID,
        data: TestPointCreate | None = None,
        *,
        group_name: str = "",
        title: str = "",
        description: str | None = None,
        priority: str = "P1",
        estimated_cases: int = 3,
        source: str = "ai",
    ) -> TestPoint:
        if data:
            tp = TestPoint(
                scene_map_id=scene_map_id,
                source=data.source or "user_added",
                **data.model_dump(exclude={"source"}),
            )
        else:
            tp = TestPoint(
                scene_map_id=scene_map_id,
                group_name=group_name,
                title=title,
                description=description,
                priority=priority,
                estimated_cases=estimated_cases,
                source=source,
                status="ai_generated" if source == "ai" else "confirmed",
            )
        self.session.add(tp)
        await self.session.commit()
        await self.session.refresh(tp)
        return tp

    async def update_test_point(
        self,
        tp_or_id: TestPoint | UUID,
        data: TestPointUpdate | None = None,
        **kwargs: object,
    ) -> TestPoint | None:
        if isinstance(tp_or_id, UUID):
            tp = await self.session.get(TestPoint, tp_or_id)
            if not tp:
                return None
        else:
            tp = tp_or_id

        if data:
            for field, value in data.model_dump(exclude_none=True).items():
                setattr(tp, field, value)
        else:
            for key, value in kwargs.items():
                if hasattr(tp, key) and value is not None:
                    setattr(tp, key, value)

        await self.session.commit()
        await self.session.refresh(tp)
        return tp

    async def confirm_test_point(self, test_point_id: UUID) -> TestPoint | None:
        return await self.update_test_point(test_point_id, status="confirmed")

    async def soft_delete_test_point(self, tp_or_id: TestPoint | UUID) -> bool:
        if isinstance(tp_or_id, UUID):
            tp = await self.session.get(TestPoint, tp_or_id)
            if not tp:
                return False
        else:
            tp = tp_or_id
        tp.deleted_at = datetime.now(UTC)
        await self.session.commit()
        return True

    async def get_test_point(self, tp_id: UUID) -> TestPoint | None:
        q = select(TestPoint).where(TestPoint.id == tp_id, TestPoint.deleted_at.is_(None))
        result = await self.session.execute(q)
        return result.scalar_one_or_none()

    async def confirm_all(self, scene_map_id: UUID) -> SceneMap | None:
        q = select(TestPoint).where(
            TestPoint.scene_map_id == scene_map_id,
            TestPoint.deleted_at.is_(None),
        )
        result = await self.session.execute(q)
        for tp in result.scalars().all():
            tp.status = "confirmed"

        scene_map = await self.session.get(SceneMap, scene_map_id)
        if scene_map:
            scene_map.status = "confirmed"
            scene_map.confirmed_at = datetime.now(UTC)
        await self.session.commit()
        if scene_map:
            await self.session.refresh(scene_map)
        return scene_map

    async def generate_stream(self, requirement_id: UUID) -> AsyncIterator[str]:
        req = await self.session.get(Requirement, requirement_id)
        content = json.dumps(req.content_ast, ensure_ascii=False) if req else ""
        title = req.title if req else ""
        user_content = (
            f"请为以下需求生成测试点列表：\n\n"
            f"需求标题：{title}\n\n"
            f"需求内容：\n{content}\n\n"
            f"请按照正常流程、异常场景、边界值、并发场景、权限安全分组，"
            f"每个测试点包含：分组名、标题、描述、优先级(P0/P1/P2)、预计用例数。"
        )
        task_instruction = "根据需求文档提取完整的测试点列表，按场景类型分组，输出 JSON 数组。"
        system = assemble_prompt("scene_map", task_instruction)
        messages = [{"role": "user", "content": user_content}]
        return await get_thinking_stream(messages, system=system)
