"""B-M12-09 — ExportService 单元测试"""

from __future__ import annotations

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ── Helpers ──────────────────────────────────────────────────────────


def _make_testcase_dict(title: str = "用例A", steps: list | None = None):
    """构造 _get_cases 返回的 dict 格式用例。"""
    return {
        "case_id": f"TC-{uuid.uuid4().hex[:6]}",
        "title": title,
        "priority": "P1",
        "case_type": "functional",
        "status": "approved",
        "precondition": "用户已登录",
        "steps": steps or [
            {"step_num": 1, "action": "点击按钮", "expected_result": "弹出对话框"},
        ],
        "tags": ["登录"],
        "module_path": "用户管理/登录",
        "source": "manual",
    }


def _make_service(session: AsyncMock):
    from app.modules.export.service import ExportService

    return ExportService(session)


# ── Tests ────────────────────────────────────────────────────────────


class TestExcelExport:
    async def test_excel_export_json_format(self):
        """JSON 格式导出应返回包含用例的 JSON 字符串。"""
        cases = [_make_testcase_dict("用例A"), _make_testcase_dict("用例B")]

        session = AsyncMock()
        svc = _make_service(session)

        with patch.object(svc, "_get_cases", return_value=cases):
            result = await svc.export_cases_json(requirement_id=uuid.uuid4())

        assert isinstance(result, str)
        parsed = json.loads(result)
        assert len(parsed) == 2
        assert parsed[0]["title"] == "用例A"

    async def test_excel_export_empty(self):
        """无用例时 JSON 导出应返回空数组字符串。"""
        session = AsyncMock()
        svc = _make_service(session)

        with patch.object(svc, "_get_cases", return_value=[]):
            result = await svc.export_cases_json(requirement_id=uuid.uuid4())

        assert result == "[]"


class TestMarkdownExport:
    async def test_csv_export(self):
        """CSV 格式导出应返回正确的 CSV 字符串。"""
        cases = [_make_testcase_dict("用例A")]

        session = AsyncMock()
        svc = _make_service(session)

        with patch.object(svc, "_get_cases", return_value=cases):
            result = await svc.export_cases_csv(requirement_id=uuid.uuid4())

        assert isinstance(result, str)
        assert "用例A" in result
        assert "case_id" in result  # header row

    async def test_csv_export_empty(self):
        """无用例时 CSV 导出应只有表头。"""
        session = AsyncMock()
        svc = _make_service(session)

        with patch.object(svc, "_get_cases", return_value=[]):
            result = await svc.export_cases_csv(requirement_id=uuid.uuid4())

        assert "case_id" in result
        lines = result.strip().split("\n")
        assert len(lines) == 1  # only header
