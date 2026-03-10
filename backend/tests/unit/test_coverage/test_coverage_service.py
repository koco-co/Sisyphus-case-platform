"""B-M08-02 — CoverageService 单元测试。"""

from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock


def _scalars_result(items):
    result = MagicMock()
    result.scalars.return_value.all.return_value = items
    return result


class TestProductCoverage:
    async def test_get_product_coverage_aggregates_iteration_requirements(self):
        """产品级覆盖聚合应返回迭代、需求、测试点与用例映射。"""
        from app.modules.coverage.service import CoverageService

        product_id = uuid.uuid4()
        iteration_id = uuid.uuid4()
        req_covered_id = uuid.uuid4()
        req_uncovered_id = uuid.uuid4()
        scene_map_id = uuid.uuid4()
        test_point_id = uuid.uuid4()
        test_case_id = uuid.uuid4()

        iteration = SimpleNamespace(id=iteration_id, name="2026-W10")
        req_covered = SimpleNamespace(
            id=req_covered_id,
            iteration_id=iteration_id,
            req_id="REQ-001",
            title="登录能力",
        )
        req_uncovered = SimpleNamespace(
            id=req_uncovered_id,
            iteration_id=iteration_id,
            req_id="REQ-002",
            title="退出登录",
        )
        scene_map = SimpleNamespace(id=scene_map_id, requirement_id=req_covered_id)
        test_point = SimpleNamespace(
            id=test_point_id,
            scene_map_id=scene_map_id,
            title="正常登录",
            priority="P1",
        )
        test_case = SimpleNamespace(
            id=test_case_id,
            requirement_id=req_covered_id,
            scene_node_id=test_point_id,
            case_id="TC-001",
            title="应允许合法账号登录",
            status="approved",
        )

        session = AsyncMock()
        session.execute = AsyncMock(
            side_effect=[
                _scalars_result([iteration]),
                _scalars_result([req_covered, req_uncovered]),
                _scalars_result([scene_map]),
                _scalars_result([test_point]),
                _scalars_result([test_case]),
            ]
        )

        service = CoverageService(session)

        payload = await service.get_product_coverage(product_id)

        assert payload == {
            "iterations": [
                {
                    "iteration_id": str(iteration_id),
                    "iteration_name": "2026-W10",
                    "coverage_rate": 50,
                    "requirement_count": 2,
                    "testcase_count": 1,
                    "uncovered_count": 1,
                    "requirements": [
                        {
                            "id": str(req_covered_id),
                            "req_id": "REQ-001",
                            "title": "登录能力",
                            "coverage_status": "full",
                            "test_points": [
                                {
                                    "id": str(test_point_id),
                                    "title": "正常登录",
                                    "priority": "P1",
                                    "case_count": 1,
                                    "cases": [
                                        {
                                            "id": str(test_case_id),
                                            "case_id": "TC-001",
                                            "title": "应允许合法账号登录",
                                            "status": "approved",
                                        }
                                    ],
                                }
                            ],
                        },
                        {
                            "id": str(req_uncovered_id),
                            "req_id": "REQ-002",
                            "title": "退出登录",
                            "coverage_status": "none",
                            "test_points": [],
                        },
                    ],
                }
            ]
        }
