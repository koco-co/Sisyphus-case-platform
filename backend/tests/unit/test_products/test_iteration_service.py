"""B-M00-14 — IterationService 单元测试"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.modules.products.schemas import IterationCreate, IterationUpdate


# ── Helpers ──────────────────────────────────────────────────────────


def _make_iteration(
    name: str = "Sprint-1",
    product_id: uuid.UUID | None = None,
    status: str = "active",
):
    it = MagicMock()
    it.id = uuid.uuid4()
    it.product_id = product_id or uuid.uuid4()
    it.name = name
    it.start_date = None
    it.end_date = None
    it.status = status
    it.deleted_at = None
    return it


def _make_service(session: AsyncMock):
    from app.modules.products.service import IterationService

    return IterationService(session)


# ── Tests ────────────────────────────────────────────────────────────


class TestCreateIteration:
    async def test_create_iteration(self):
        session = AsyncMock()
        iter_mock = _make_iteration()
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()

        svc = _make_service(session)

        with patch("app.modules.products.service.Iteration", return_value=iter_mock):
            result = await svc.create_iteration(
                IterationCreate(product_id=iter_mock.product_id, name="Sprint-1")
            )

        session.add.assert_called_once_with(iter_mock)
        session.commit.assert_awaited_once()
        session.refresh.assert_awaited_once_with(iter_mock)
        assert result == iter_mock

    async def test_create_iteration_with_dates(self):
        session = AsyncMock()
        iter_mock = _make_iteration()
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()

        svc = _make_service(session)

        with patch("app.modules.products.service.Iteration", return_value=iter_mock):
            result = await svc.create_iteration(
                IterationCreate(
                    product_id=iter_mock.product_id,
                    name="Sprint-2",
                    start_date="2024-01-01",
                    end_date="2024-01-14",
                )
            )

        assert result == iter_mock


class TestListIterations:
    async def test_list_by_product(self):
        product_id = uuid.uuid4()
        iterations = [_make_iteration("S1", product_id), _make_iteration("S2", product_id)]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = iterations

        session = AsyncMock()
        session.execute = AsyncMock(return_value=mock_result)

        svc = _make_service(session)
        result = await svc.list_by_product(product_id)

        assert len(result) == 2
        assert result[0].name == "S1"
        assert result[1].name == "S2"

    async def test_list_by_product_empty(self):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []

        session = AsyncMock()
        session.execute = AsyncMock(return_value=mock_result)

        svc = _make_service(session)
        result = await svc.list_by_product(uuid.uuid4())

        assert result == []


class TestUpdateIteration:
    async def test_update_iteration(self):
        it = _make_iteration()
        session = AsyncMock()
        session.get = AsyncMock(return_value=it)
        session.commit = AsyncMock()
        session.refresh = AsyncMock()

        svc = _make_service(session)
        result = await svc.update_iteration(it.id, IterationUpdate(name="Updated"))

        assert result.name == "Updated"
        session.commit.assert_awaited_once()

    async def test_update_iteration_status(self):
        it = _make_iteration()
        session = AsyncMock()
        session.get = AsyncMock(return_value=it)
        session.commit = AsyncMock()
        session.refresh = AsyncMock()

        svc = _make_service(session)
        result = await svc.update_iteration(it.id, IterationUpdate(status="completed"))

        assert result.status == "completed"

    async def test_update_iteration_not_found(self):
        session = AsyncMock()
        session.get = AsyncMock(return_value=None)

        svc = _make_service(session)
        with pytest.raises(HTTPException) as exc_info:
            await svc.update_iteration(uuid.uuid4(), IterationUpdate(name="X"))

        assert exc_info.value.status_code == 404
