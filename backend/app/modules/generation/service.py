import json
import logging
from collections.abc import AsyncIterator
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.parser import parse_test_cases
from app.ai.prompts import assemble_prompt
from app.ai.sse_collector import SSECollector
from app.ai.stream_adapter import get_thinking_stream
from app.core.database import get_async_session_context
from app.modules.generation.models import GenerationMessage, GenerationSession
from app.modules.products.models import Requirement
from app.modules.scene_map.models import SceneMap, TestPoint
from app.modules.testcases.models import TestCase

logger = logging.getLogger(__name__)


async def _save_and_parse_response(
    session_id: UUID,
    requirement_id: UUID,
    full_text: str,
) -> None:
    """Persist assistant message and auto-parse test cases from AI output."""
    from app.modules.testcases.schemas import TestCaseCreate, TestCaseStepSchema
    from app.modules.testcases.service import TestCaseService

    async with get_async_session_context() as new_session:
        gen_svc = GenerationService(new_session)
        await gen_svc.save_message(session_id, "assistant", full_text)

        parsed = parse_test_cases(full_text)
        if not parsed:
            return

        tc_svc = TestCaseService(new_session)
        for case in parsed:
            try:
                steps = [
                    TestCaseStepSchema(
                        step=step.get("step_num", i + 1),
                        action=step.get("action", ""),
                        expected=step.get("expected_result", ""),
                    )
                    for i, step in enumerate(case.get("steps", []))
                ]
                case_type_raw = case.get("case_type", "functional")
                valid_types = {"functional", "boundary", "exception", "performance", "security", "compatibility"}
                case_type = case_type_raw if case_type_raw in valid_types else "functional"

                data = TestCaseCreate(
                    requirement_id=requirement_id,
                    generation_session_id=session_id,
                    title=case.get("title", ""),
                    priority=case.get("priority", "P1"),
                    case_type=case_type,  # type: ignore[arg-type]
                    precondition=case.get("precondition", ""),
                    source="ai_generated",
                    steps=steps,
                )
                await tc_svc.create_case(data)
            except Exception:
                logger.warning("Failed to save parsed test case: %s", case.get("title", ""))


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

    async def get_or_create_session(self, requirement_id: UUID, mode: str = "test_point_driven") -> GenerationSession:
        """Return the latest active session for a requirement, or create one."""
        q = (
            select(GenerationSession)
            .where(
                GenerationSession.requirement_id == requirement_id,
                GenerationSession.mode == mode,
                GenerationSession.status == "active",
                GenerationSession.deleted_at.is_(None),
            )
            .order_by(GenerationSession.created_at.desc())
            .limit(1)
        )
        result = await self.session.execute(q)
        existing = result.scalar_one_or_none()
        if existing:
            return existing
        return await self.create_session(requirement_id, mode)

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

    async def list_session_cases(self, session_id: UUID) -> list[TestCase]:
        q = (
            select(TestCase)
            .where(
                TestCase.generation_session_id == session_id,
                TestCase.deleted_at.is_(None),
            )
            .order_by(TestCase.created_at.desc())
        )
        result = await self.session.execute(q)
        return list(result.scalars().all())

    async def accept_session_case(self, session_id: UUID, case_id: UUID) -> TestCase:
        q = select(TestCase).where(
            TestCase.id == case_id,
            TestCase.generation_session_id == session_id,
            TestCase.deleted_at.is_(None),
        )
        result = await self.session.execute(q)
        test_case = result.scalar_one_or_none()
        if not test_case:
            raise ValueError("Test case not found")

        if test_case.status == "draft":
            test_case.status = "review"
            await self.session.commit()
            await self.session.refresh(test_case)

        return test_case

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

        # On first turn, inject context into the user message
        if len(messages) <= 1 and context_parts:
            context = "\n\n".join(context_parts)
            enriched = f"{context}\n\n用户请求：{user_message}"
            if history:
                history[-1]["content"] = enriched
            else:
                history.append({"role": "user", "content": enriched})

        # In test_point_driven mode without test points, warn the user
        if (
            gen_session.mode == "test_point_driven"
            and not scene_map
            and not any("测试点" in msg.get("content", "") for msg in history)
        ):
            history.append(
                {
                    "role": "system",
                    "content": "注意：当前需求尚未生成测试点/场景地图，建议先完成 M04 测试点分析后再进入用例生成。",
                }
            )

        # Select prompt module based on session mode
        if gen_session.mode == "test_point_driven":
            task_instruction = "根据已确认的测试点，生成高质量、可执行的测试用例，输出 JSON 数组。"
            system = assemble_prompt("generation", task_instruction)
        else:
            task_instruction = "与用户协作完成测试用例设计，根据对话上下文生成或调整用例。"
            system = assemble_prompt("exploratory", task_instruction)
        return await get_thinking_stream(history, system=system)

    # ── SSE stream with auto-persistence ──────────────────────────────

    async def chat_and_persist_stream(self, session_id: UUID, user_message: str) -> SSECollector:
        """Chat with AI and auto-persist response + parsed test cases on completion."""
        gen_session = await self.get_session(session_id)
        if not gen_session:
            raise ValueError("Session not found")
        await self.save_message(session_id, "user", user_message)
        stream = await self.chat_stream(session_id, user_message)

        req_id = gen_session.requirement_id

        async def on_complete(full_text: str) -> None:
            await _save_and_parse_response(session_id, req_id, full_text)

        return SSECollector(stream, on_complete=on_complete)

    async def chat_by_requirement_and_persist_stream(self, requirement_id: UUID, user_message: str) -> SSECollector:
        """Chat by requirement with auto-persistence; creates session if needed."""
        gen_session = await self.get_or_create_session(requirement_id)
        sid = gen_session.id
        await self.save_message(sid, "user", user_message)
        stream = await self.chat_stream(sid, user_message)

        async def on_complete(full_text: str) -> None:
            await _save_and_parse_response(sid, requirement_id, full_text)

        return SSECollector(stream, on_complete=on_complete)

    async def template_and_persist_stream(
        self,
        requirement_id: UUID,
        template_id: UUID,
        variables: dict[str, str] | None = None,
    ) -> SSECollector:
        """Template-driven case generation stream with auto-persistence."""
        from app.engine.case_gen.template_driven import template_driven_stream
        from app.modules.templates.models import TestCaseTemplate

        tpl_q = select(TestCaseTemplate).where(
            TestCaseTemplate.id == template_id,
            TestCaseTemplate.deleted_at.is_(None),
        )
        tpl_result = await self.session.execute(tpl_q)
        template = tpl_result.scalar_one_or_none()
        if not template:
            raise ValueError("Template not found")

        req = await self.session.get(Requirement, requirement_id)
        if not req:
            raise ValueError("Requirement not found")

        req_content = json.dumps(req.content_ast, ensure_ascii=False) if req.content_ast else ""

        gen_session = await self.get_or_create_session(requirement_id, mode="template_driven")
        sid = gen_session.id

        stream = await template_driven_stream(
            template_name=template.name,
            template_category=template.category,
            template_description=template.description or "",
            template_content=template.template_content,
            template_variables=template.variables,
            user_variables=variables,
            requirement_title=req.title,
            requirement_content=req_content,
        )

        async def on_complete(full_text: str) -> None:
            await _save_and_parse_response(sid, requirement_id, full_text)

        return SSECollector(stream, on_complete=on_complete)
