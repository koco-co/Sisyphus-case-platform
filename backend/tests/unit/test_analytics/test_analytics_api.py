"""Analytics API contract tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from httpx import ASGITransport, AsyncClient


class TestAnalyticsTrendEndpoint:
    async def test_global_trends_match_frontend_contract(self):
        """GET /api/analytics/trends 应返回前端趋势图所需结构。"""
        payload = {
            "case_count_trend": [
                {"date": "03/08", "value": 12},
                {"date": "03/09", "value": 18},
            ],
            "pass_rate_trend": [
                {"date": "03/08", "value": 66.67},
                {"date": "03/09", "value": 80.0},
            ],
        }
        mock_service_instance = AsyncMock()
        mock_service_instance.get_frontend_trends = AsyncMock(return_value=payload)

        with patch("app.modules.analytics.router.AnalyticsService", return_value=mock_service_instance):
            from app.core.database import get_async_session
            from app.main import app

            async def _override():
                yield AsyncMock()

            app.dependency_overrides[get_async_session] = _override
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                resp = await ac.get("/api/analytics/trends")

            app.dependency_overrides.clear()

        assert resp.status_code == 200
        assert resp.json() == payload
