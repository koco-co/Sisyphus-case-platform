"""B-M06-08 — TestCaseService 单元测试"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from sqlalchemy.dialects import postgresql

from app.modules.testcases.schemas import TestCaseCreate

# ── Helpers ──────────────────────────────────────────────────────────


def _make_testcase(
    title: str = "登录功能正常流程",
    priority: str = "P1",
    status: str = "draft",
    version: int = 1,
):
    tc = MagicMock()
    tc.id = uuid.uuid4()
    tc.requirement_id = uuid.uuid4()
    tc.scene_node_id = None
    tc.generation_session_id = None
    tc.case_id = f"TC-{uuid.uuid4().hex[:6]}"
    tc.title = title
    tc.module_path = None
    tc.precondition = "用户已注册"
    tc.priority = priority
    tc.case_type = "functional"
    tc.status = status
    tc.source = "manual"
    tc.steps = []
    tc.tags = []
    tc.ai_score = None
    tc.created_by = None
    tc.reviewer_id = None
    tc.review_comment = None
    tc.version = version
    tc.deleted_at = None
    tc.created_at = "2024-01-01T00:00:00"
    tc.updated_at = "2024-01-01T00:00:00"
    return tc


def _make_service(session: AsyncMock):
    from app.modules.testcases.service import TestCaseService

    return TestCaseService(session)


def _compile_sql(statement) -> str:
    return str(
        statement.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    )


# ── Tests ────────────────────────────────────────────────────────────


class TestCreateTestcase:
    async def test_create_testcase(self):
        """创建用例应持久化并返回对象。"""
        session = AsyncMock()
        tc_mock = _make_testcase()
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.flush = AsyncMock()

        # Mock execute for idempotency check
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute = AsyncMock(return_value=mock_result)

        svc = _make_service(session)

        with patch("app.modules.testcases.service.TestCase", return_value=tc_mock):
            result = await svc.create_case(
                TestCaseCreate(
                    requirement_id=tc_mock.requirement_id,
                    title="登录功能正常流程",
                )
            )

        assert result.title == "登录功能正常流程"
        session.commit.assert_awaited_once()

    async def test_create_testcase_idempotent(self):
        """重复 case_id 应返回已有记录（幂等）。"""
        existing_tc = _make_testcase()
        existing_tc.case_id = "TC-001"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_tc

        session = AsyncMock()
        session.execute = AsyncMock(return_value=mock_result)

        svc = _make_service(session)
        result = await svc.create_case(
            TestCaseCreate(
                requirement_id=existing_tc.requirement_id,
                title="测试",
                case_id="TC-001",
            )
        )

        assert result.case_id == "TC-001"
        session.add.assert_not_called()


class TestListWithFilters:
    async def test_list_with_filters(self):
        """带过滤条件的列表查询应正常返回 (items, total) 元组。"""
        cases = [_make_testcase("用例A", "P0"), _make_testcase("用例B", "P1")]

        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 2

        mock_list_result = MagicMock()
        mock_list_result.scalars.return_value.all.return_value = cases

        session = AsyncMock()
        session.execute = AsyncMock(side_effect=[mock_count_result, mock_list_result])

        svc = _make_service(session)
        items, total = await svc.list_cases(
            requirement_id=cases[0].requirement_id,
            page=1,
            page_size=20,
        )

        assert total == 2
        assert len(items) == 2

    async def test_list_empty(self):
        """无匹配项时应返回空列表。"""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        mock_list_result = MagicMock()
        mock_list_result.scalars.return_value.all.return_value = []

        session = AsyncMock()
        session.execute = AsyncMock(side_effect=[mock_count_result, mock_list_result])

        svc = _make_service(session)
        items, total = await svc.list_cases(
            requirement_id=uuid.uuid4(),
            page=1,
            page_size=20,
        )

        assert total == 0
        assert items == []

    async def test_list_keyword_matches_case_id(self):
        """关键字搜索应同时匹配标题和 case_id。"""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        mock_list_result = MagicMock()
        mock_list_result.scalars.return_value.all.return_value = []

        session = AsyncMock()
        session.execute = AsyncMock(side_effect=[mock_count_result, mock_list_result])

        svc = _make_service(session)
        await svc.list_cases(keyword="TC-001", page=1, page_size=20)

        count_stmt = session.execute.await_args_list[0].args[0]
        sql = _compile_sql(count_stmt)

        assert "test_cases.title ILIKE '%%TC-001%%'" in sql
        assert "test_cases.case_id ILIKE '%%TC-001%%'" in sql

    async def test_list_aliases_functional_ai_generated_and_review_status(self):
        """列表过滤应兼容旧状态、类型和来源别名。"""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        mock_list_result = MagicMock()
        mock_list_result.scalars.return_value.all.return_value = []

        session = AsyncMock()
        session.execute = AsyncMock(side_effect=[mock_count_result, mock_list_result])

        svc = _make_service(session)
        await svc.list_cases(
            status_filter="review",
            case_type="functional",
            source="ai_generated",
            page=1,
            page_size=20,
        )

        count_stmt = session.execute.await_args_list[0].args[0]
        sql = _compile_sql(count_stmt)

        assert "test_cases.status IN ('review', 'pending_review')" in sql
        assert "test_cases.case_type IN ('functional', 'normal')" in sql
        assert "test_cases.source IN ('ai_generated', 'ai')" in sql


class TestVersionHistory:
    async def test_version_history(self):
        """版本历史应正确返回。"""
        tc_id = uuid.uuid4()

        v1 = MagicMock()
        v1.id = uuid.uuid4()
        v1.test_case_id = tc_id
        v1.version = 1
        v1.snapshot = {"title": "v1 title"}
        v1.change_reason = "初始创建"

        v2 = MagicMock()
        v2.id = uuid.uuid4()
        v2.test_case_id = tc_id
        v2.version = 2
        v2.snapshot = {"title": "v2 title"}
        v2.change_reason = "更新步骤"

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [v1, v2]

        session = AsyncMock()
        session.execute = AsyncMock(return_value=mock_result)

        svc = _make_service(session)
        result = await svc.list_versions(tc_id)

        assert len(result) == 2
        assert result[0].version == 1
        assert result[1].version == 2
