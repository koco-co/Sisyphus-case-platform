"""T-UNIT-02 — RequirementService 单元测试"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.modules.products.schemas import RequirementCreate


# ── Helpers ──────────────────────────────────────────────────────────


def _make_requirement(
    req_id: str = "REQ-001",
    title: str = "Test Requirement",
    iteration_id: uuid.UUID | None = None,
):
    req = MagicMock()
    req.id = uuid.uuid4()
    req.req_id = req_id
    req.title = title
    req.iteration_id = iteration_id or uuid.uuid4()
    req.content_ast = {}
    req.frontmatter = None
    req.status = "draft"
    req.version = 1
    req.deleted_at = None
    return req


def _make_service(session: AsyncMock):
    from app.modules.products.service import RequirementService

    return RequirementService(session)


# ── Tests ────────────────────────────────────────────────────────────


class TestCreateRequirement:
    async def test_create_requirement(self):
        session = AsyncMock()
        req_mock = _make_requirement()
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()

        svc = _make_service(session)
        iteration_id = uuid.uuid4()

        with patch("app.modules.products.service.Requirement", return_value=req_mock):
            result = await svc.create_requirement(
                RequirementCreate(
                    iteration_id=iteration_id,
                    req_id="REQ-001",
                    title="Test Requirement",
                )
            )

        session.add.assert_called_once_with(req_mock)
        session.commit.assert_awaited_once()
        assert result.req_id == "REQ-001"

    async def test_create_requirement_with_ast(self):
        session = AsyncMock()
        req_mock = _make_requirement()
        req_mock.content_ast = {"sections": [{"heading": "A", "body": "B"}]}
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()

        svc = _make_service(session)

        with patch("app.modules.products.service.Requirement", return_value=req_mock):
            result = await svc.create_requirement(
                RequirementCreate(
                    iteration_id=uuid.uuid4(),
                    req_id="REQ-002",
                    title="With AST",
                    content_ast={"sections": [{"heading": "A", "body": "B"}]},
                )
            )

        assert result.content_ast == {"sections": [{"heading": "A", "body": "B"}]}


class TestGetRequirementById:
    async def test_get_requirement_by_id_via_list(self):
        """通过 list_all 获取需求并验证字段。"""
        req = _make_requirement(req_id="REQ-099", title="Specific Req")

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [req]

        session = AsyncMock()
        session.execute = AsyncMock(return_value=mock_result)

        svc = _make_service(session)
        results = await svc.list_all()

        assert len(results) == 1
        assert results[0].req_id == "REQ-099"
        assert results[0].title == "Specific Req"


class TestSoftDeleteRequirement:
    async def test_soft_delete_requirement(self):
        req = _make_requirement()
        session = AsyncMock()
        session.get = AsyncMock(return_value=req)
        session.commit = AsyncMock()

        svc = _make_service(session)
        await svc.soft_delete_requirement(req.id)

        assert req.deleted_at is not None
        session.commit.assert_awaited_once()

    async def test_soft_delete_requirement_not_found(self):
        session = AsyncMock()
        session.get = AsyncMock(return_value=None)

        svc = _make_service(session)
        with pytest.raises(HTTPException) as exc_info:
            await svc.soft_delete_requirement(uuid.uuid4())

        assert exc_info.value.status_code == 404

    async def test_soft_delete_requirement_already_deleted(self):
        req = _make_requirement()
        req.deleted_at = "2024-01-01"

        session = AsyncMock()
        session.get = AsyncMock(return_value=req)

        svc = _make_service(session)
        with pytest.raises(HTTPException) as exc_info:
            await svc.soft_delete_requirement(req.id)

        assert exc_info.value.status_code == 404
