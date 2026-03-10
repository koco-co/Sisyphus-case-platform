import json
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from itertools import groupby
from uuid import UUID

from fastapi import HTTPException
from fastapi import status as http_status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.parser import parse_test_points
from app.ai.prompts import assemble_prompt
from app.ai.sse_collector import SSECollector
from app.ai.stream_adapter import get_thinking_stream
from app.core.database import get_async_session_context
from app.modules.products.models import Requirement
from app.modules.scene_map.models import SceneMap, TestPoint
from app.modules.scene_map.schemas import BatchPointUpdate, ReorderItem, TestPointCreate, TestPointUpdate


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

    async def get_map_by_id(self, map_id: UUID) -> SceneMap | None:
        q = select(SceneMap).where(
            SceneMap.id == map_id,
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
            .order_by(TestPoint.sort_order, TestPoint.group_name, TestPoint.created_at)
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

    # ── Batch operations (B-M04-09) ───────────────────────────────

    async def batch_update_points(self, updates: list[BatchPointUpdate]) -> list[TestPoint]:
        updated: list[TestPoint] = []
        for item in updates:
            tp = await self.session.get(TestPoint, item.id)
            if not tp or tp.deleted_at is not None:
                continue
            for field, value in item.model_dump(exclude={"id"}, exclude_none=True).items():
                setattr(tp, field, value)
            updated.append(tp)
        await self.session.commit()
        for tp in updated:
            await self.session.refresh(tp)
        return updated

    async def reorder_points(self, map_id: UUID, order: list[ReorderItem]) -> list[TestPoint]:
        scene_map = await self.get_map_by_id(map_id)
        if not scene_map:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Scene map not found",
            )
        order_map = {item.id: item.sort_order for item in order}
        points = await self.list_test_points(map_id)
        for tp in points:
            if tp.id in order_map:
                tp.sort_order = order_map[tp.id]
        await self.session.commit()
        return await self.list_test_points(map_id)

    # ── Export (B-M04-10) ─────────────────────────────────────────

    async def export_scene_map(self, map_id: UUID, fmt: str = "json") -> dict | str:
        scene_map = await self.get_map_by_id(map_id)
        if not scene_map:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Scene map not found",
            )
        points = await self.list_test_points(map_id)

        if fmt == "json":
            return self._export_json(scene_map, points)
        elif fmt == "md":
            return self._export_markdown(scene_map, points)
        else:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported format: {fmt}. Use 'json' or 'md'.",
            )

    def _export_json(self, scene_map: SceneMap, points: list[TestPoint]) -> dict:
        return {
            "scene_map": {
                "id": str(scene_map.id),
                "requirement_id": str(scene_map.requirement_id),
                "status": scene_map.status,
                "confirmed_at": scene_map.confirmed_at.isoformat() if scene_map.confirmed_at else None,
            },
            "test_points": [
                {
                    "id": str(tp.id),
                    "group_name": tp.group_name,
                    "title": tp.title,
                    "description": tp.description,
                    "priority": tp.priority,
                    "status": tp.status,
                    "estimated_cases": tp.estimated_cases,
                    "source": tp.source,
                }
                for tp in points
            ],
        }

    def _export_markdown(self, scene_map: SceneMap, points: list[TestPoint]) -> str:
        lines: list[str] = [
            f"# 场景地图 — {scene_map.status}",
            "",
            f"- **ID**: `{scene_map.id}`",
            f"- **需求 ID**: `{scene_map.requirement_id}`",
            f"- **状态**: {scene_map.status}",
            "",
        ]
        sorted_points = sorted(points, key=lambda p: p.group_name)
        for group, group_points in groupby(sorted_points, key=lambda p: p.group_name):
            lines.append(f"## {group}")
            lines.append("")
            for tp in group_points:
                priority_badge = f"[{tp.priority}]"
                lines.append(f"- {priority_badge} **{tp.title}**")
                if tp.description:
                    lines.append(f"  - 描述: {tp.description}")
                lines.append(f"  - 预计用例数: {tp.estimated_cases} | 来源: {tp.source} | 状态: {tp.status}")
            lines.append("")

        return "\n".join(lines)

    # ── AI generation ─────────────────────────────────────────────

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

    async def generate_stream_with_persistence(self, requirement_id: UUID) -> SSECollector:
        """Generate scene map stream; auto-persist parsed test points on completion."""
        scene_map = await self.get_or_create(requirement_id)
        scene_map_id = scene_map.id
        stream = await self.generate_stream(requirement_id)

        async def on_complete(full_text: str) -> None:
            async with get_async_session_context() as new_session:
                new_svc = SceneMapService(new_session)
                points = parse_test_points(full_text)
                for pt in points:
                    await new_svc.add_test_point(
                        scene_map_id,
                        group_name=pt["group_name"],
                        title=pt["title"],
                        description=pt.get("description"),
                        priority=pt.get("priority", "P1"),
                        estimated_cases=pt.get("estimated_cases", 3),
                        source="ai",
                    )

        return SSECollector(stream, on_complete=on_complete)
