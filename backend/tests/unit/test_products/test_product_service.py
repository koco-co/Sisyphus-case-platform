"""T-UNIT-02 — ProductService 单元测试"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.modules.products.schemas import ProductCreate, ProductUpdate


# ── Helpers ──────────────────────────────────────────────────────────


def _make_product(name: str = "TestProduct", slug: str = "test-product", description: str | None = None):
    """构造一个伪 Product ORM 对象。"""
    product = MagicMock()
    product.id = uuid.uuid4()
    product.name = name
    product.slug = slug
    product.description = description
    product.deleted_at = None
    return product


def _make_service(session: AsyncMock):
    from app.modules.products.service import ProductService

    return ProductService(session)


# ── Tests ────────────────────────────────────────────────────────────


class TestCreateProduct:
    async def test_create_product(self):
        session = AsyncMock()
        product_mock = _make_product()
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()

        svc = _make_service(session)

        with patch("app.modules.products.service.Product", return_value=product_mock) as MockProduct:
            result = await svc.create_product(ProductCreate(name="TestProduct", slug="test-product"))

        session.add.assert_called_once_with(product_mock)
        session.commit.assert_awaited_once()
        session.refresh.assert_awaited_once_with(product_mock)
        assert result == product_mock


class TestListProducts:
    async def test_list_products(self):
        products = [_make_product("A", "a"), _make_product("B", "b")]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = products

        session = AsyncMock()
        session.execute = AsyncMock(return_value=mock_result)

        svc = _make_service(session)
        result = await svc.list_products()

        assert len(result) == 2
        assert result[0].name == "A"
        assert result[1].slug == "b"

    async def test_list_products_empty(self):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []

        session = AsyncMock()
        session.execute = AsyncMock(return_value=mock_result)

        svc = _make_service(session)
        result = await svc.list_products()

        assert result == []


class TestSoftDeleteProduct:
    async def test_soft_delete_product(self):
        product = _make_product()
        session = AsyncMock()
        session.get = AsyncMock(return_value=product)
        session.commit = AsyncMock()

        svc = _make_service(session)
        await svc.soft_delete_product(product.id)

        assert product.deleted_at is not None
        session.commit.assert_awaited_once()

    async def test_soft_delete_product_not_found(self):
        session = AsyncMock()
        session.get = AsyncMock(return_value=None)

        svc = _make_service(session)
        with pytest.raises(HTTPException) as exc_info:
            await svc.soft_delete_product(uuid.uuid4())

        assert exc_info.value.status_code == 404

    async def test_soft_delete_already_deleted(self):
        product = _make_product()
        product.deleted_at = "2024-01-01"  # already deleted

        session = AsyncMock()
        session.get = AsyncMock(return_value=product)

        svc = _make_service(session)
        with pytest.raises(HTTPException) as exc_info:
            await svc.soft_delete_product(product.id)

        assert exc_info.value.status_code == 404


class TestUpdateProduct:
    async def test_update_product(self):
        product = _make_product()
        session = AsyncMock()
        session.get = AsyncMock(return_value=product)
        session.commit = AsyncMock()
        session.refresh = AsyncMock()

        svc = _make_service(session)
        result = await svc.update_product(
            product.id,
            ProductUpdate(name="Updated"),
        )

        assert result.name == "Updated"
        session.commit.assert_awaited_once()

    async def test_update_product_not_found(self):
        session = AsyncMock()
        session.get = AsyncMock(return_value=None)

        svc = _make_service(session)
        with pytest.raises(HTTPException) as exc_info:
            await svc.update_product(uuid.uuid4(), ProductUpdate(name="X"))

        assert exc_info.value.status_code == 404
