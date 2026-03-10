"""B-M08-01 — Coverage API contract tests."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, patch

from httpx import ASGITransport, AsyncClient


class TestCoverageProductEndpoint:
    async def test_product_coverage_matches_frontend_contract(self):
        """GET /api/coverage/product/{product_id} 应返回覆盖矩阵页面需要的聚合结构。"""
        product_id = uuid.uuid4()
        payload = {
            "iterations": [
                {
                    "iteration_id": str(uuid.uuid4()),
                    "iteration_name": "2026-W10",
                    "coverage_rate": 50,
                    "requirement_count": 2,
                    "testcase_count": 1,
                    "uncovered_count": 1,
                    "requirements": [
                        {
                            "id": str(uuid.uuid4()),
                            "req_id": "REQ-001",
                            "title": "登录能力",
                            "coverage_status": "full",
                            "test_points": [
                                {
                                    "id": str(uuid.uuid4()),
                                    "title": "正常登录",
                                    "priority": "P1",
                                    "case_count": 1,
                                    "cases": [
                                        {
                                            "id": str(uuid.uuid4()),
                                            "case_id": "TC-001",
                                            "title": "应允许合法账号登录",
                                            "status": "approved",
                                        }
                                    ],
                                }
                            ],
                        }
                    ],
                }
            ]
        }
        mock_service_instance = AsyncMock()
        mock_service_instance.get_product_coverage = AsyncMock(return_value=payload)

        with patch("app.modules.coverage.router.CoverageService", return_value=mock_service_instance):
            from app.core.database import get_async_session
            from app.main import app

            async def _override():
                yield AsyncMock()

            app.dependency_overrides[get_async_session] = _override
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                resp = await ac.get(f"/api/coverage/product/{product_id}")

            app.dependency_overrides.clear()

        assert resp.status_code == 200
        assert resp.json() == payload
