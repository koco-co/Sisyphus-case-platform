"""DiagnosisService 回归测试。"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

from app.modules.diagnosis.service import DiagnosisService


def _make_report():
    report = MagicMock()
    report.id = uuid.uuid4()
    report.status = "running"
    report.summary = None
    report.risk_count_high = 1
    report.risk_count_medium = 2
    report.risk_count_industry = 3
    report.overall_score = None
    return report


class TestPersistAiResponse:
    async def test_persist_ai_response_extracts_markdown_risks_and_score(self):
        """Markdown 风险表格应被解析并持久化为 DiagnosisRisk。"""
        report = _make_report()
        session = AsyncMock()
        session.add = MagicMock()
        session.get = AsyncMock(return_value=report)
        session.flush = AsyncMock()
        session.commit = AsyncMock()

        service = DiagnosisService(session)
        ai_content = """## 测试健康诊断报告

### 总体健康评分
- 评分：40/100

### 风险点列表
| ID | Title | Description | Risk Level | Suggestion |
| --- | --- | --- | --- | --- |
| R1 | 权限校验缺失 | 管理员与普通用户权限边界不清 | high | 补充 RBAC 校验 |
| R2 | 导入上限未定义 | 批量导入的最大记录数未说明 | medium | 明确容量上限 |
"""

        risks = await service.persist_ai_response(report.id, ai_content)

        assert len(risks) == 2
        assert risks[0].title == "权限校验缺失"
        assert risks[0].level == "high"
        assert risks[1].title == "导入上限未定义"
        assert report.risk_count_high == 1
        assert report.risk_count_medium == 1
        assert report.overall_score == 40.0


class TestCompleteReport:
    async def test_complete_report_preserves_existing_risk_counts_by_default(self):
        """仅更新 summary/status 时不应把既有风险计数重置为 0。"""
        report = _make_report()
        session = AsyncMock()
        session.get = AsyncMock(return_value=report)
        session.commit = AsyncMock()
        session.refresh = AsyncMock()

        service = DiagnosisService(session)
        await service.complete_report(report.id, summary="诊断完成")

        assert report.status == "completed"
        assert report.summary == "诊断完成"
        assert report.risk_count_high == 1
        assert report.risk_count_medium == 2
        assert report.risk_count_industry == 3
