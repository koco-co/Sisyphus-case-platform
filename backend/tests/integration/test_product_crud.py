"""集成测试桩 — 产品/迭代/需求 CRUD 流程

NOTE: 需要 Docker 环境运行（PostgreSQL + Redis）。
      运行前请确保：docker compose -f docker/docker-compose.yml up -d
"""

from __future__ import annotations

import pytest

pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.integration,
]


async def test_create_product_flow():
    """T-INT-03: 创建产品 → 创建迭代 → 创建需求 → 查询验证。"""
    pytest.skip("需要 Docker 环境（PG/Redis），请在集成测试环境中运行")


async def test_update_and_softdelete_product():
    """更新产品信息 → 软删除 → 查询确认已不可见。"""
    pytest.skip("需要 Docker 环境（PG/Redis），请在集成测试环境中运行")


async def test_requirement_upload_and_parse():
    """上传需求文档 → UDA 解析 → 结构化存储。"""
    pytest.skip("需要 Docker 环境（PG/Redis/MinIO），请在集成测试环境中运行")
