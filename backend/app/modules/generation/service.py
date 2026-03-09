import json
from collections.abc import AsyncIterator
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.prompts import GENERATION_SYSTEM
from app.ai.stream_adapter import get_thinking_stream
from app.modules.generation.models import GenerationMessage, GenerationSession
from app.modules.products.models import Requirement
from app.modules.scene_map.models import SceneMap, TestPoint


class GenerationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_session(self, requirement_id: UUID, mode: str = "test_point_driven") -> GenerationSession:
        gen_session = GenerationSession(
            requirement_id=requirement_id,
            mode=mode,
            status="active",
            model_used="glm-4-flash",
        )
        self.session.add(gen_session)
        await self.session.commit()
        await self.session.refresh(gen_session)
        return gen_session

    async def get_session(self, session_id: UUID) -> GenerationSession | None:
        q = select(GenerationSession).where(
            GenerationSession.id == session_id,
            GenerationSession.deleted_at.is_(None),
        )
        result = await self.session.execute(q)
        return result.scalar_one_or_none()

    async def list_sessions(self, requirement_id: UUID) -> list[GenerationSession]:
        q = (
            select(GenerationSession)
            .where(
                GenerationSession.requirement_id == requirement_id,
                GenerationSession.deleted_at.is_(None),
            )
            .order_by(GenerationSession.created_at.desc())
        )
        result = await self.session.execute(q)
        return list(result.scalars().all())

    async def save_message(
        self, session_id: UUID, role: str, content: str, thinking_content: str | None = None
    ) -> GenerationMessage:
        msg = GenerationMessage(
            session_id=session_id,
            role=role,
            content=content,
            thinking_content=thinking_content,
            token_count=len(content),
        )
        self.session.add(msg)
        await self.session.commit()
        await self.session.refresh(msg)
        return msg

    async def list_messages(self, session_id: UUID) -> list[GenerationMessage]:
        q = (
            select(GenerationMessage)
            .where(
                GenerationMessage.session_id == session_id,
                GenerationMessage.deleted_at.is_(None),
            )
            .order_by(GenerationMessage.created_at)
        )
        result = await self.session.execute(q)
        return list(result.scalars().all())

    async def chat_stream(self, session_id: UUID, user_message: str) -> AsyncIterator[str]:
        gen_session = await self.get_session(session_id)
        if not gen_session:
            raise ValueError("Session not found")

        # Build context from requirement
        req = await self.session.get(Requirement, gen_session.requirement_id)
        context_parts = []
        if req:
            context_parts.append(f"需求标题：{req.title}")
            content = json.dumps(req.content_ast, ensure_ascii=False) if req.content_ast else ""
            if content:
                context_parts.append(f"需求内容：{content}")

        # Get test points if available
        map_q = select(SceneMap).where(
            SceneMap.requirement_id == gen_session.requirement_id,
            SceneMap.deleted_at.is_(None),
        )
        map_result = await self.session.execute(map_q)
        scene_map = map_result.scalar_one_or_none()
        if scene_map:
            tp_q = select(TestPoint).where(
                TestPoint.scene_map_id == scene_map.id,
                TestPoint.deleted_at.is_(None),
            )
            tp_result = await self.session.execute(tp_q)
            test_points = tp_result.scalars().all()
            if test_points:
                tp_text = "\n".join(f"- [{tp.group_name}] {tp.title} (优先级: {tp.priority})" for tp in test_points)
                context_parts.append(f"已确认测试点：\n{tp_text}")

        # Build chat history (excluding latest user message, which will be appended below)
        history: list[dict[str, str]] = []
        messages = await self.list_messages(session_id)
        for msg in messages:
            history.append({"role": msg.role, "content": msg.content})

        # Inject context on first conversation turn (only 1 message = the one just saved)
        if len(messages) <= 1 and context_parts:
            context = "\n\n".join(context_parts)
            user_message = f"{context}\n\n用户请求：{user_message}"
            # Replace the last history entry with context-enriched version
            if history:
                history[-1]["content"] = user_message
        else:
            history.append({"role": "user", "content": user_message})
        return await get_thinking_stream(history, system=GENERATION_SYSTEM)
