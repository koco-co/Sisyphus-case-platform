"""T-UNIT-10 — 需求质量评估器测试"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest


class TestEvaluateQuality:
    """测试需求质量评估器（mock LLM）。"""

    async def test_evaluate_quality(self):
        """应返回包含 scores、issues、overall 的评估结果。"""
        mock_result = AsyncMock()
        mock_result.content = """
        分析结果如下：
        ```json
        {
          "scores": {
            "completeness": 85,
            "clarity": 70,
            "testability": 60,
            "consistency": 90
          },
          "issues": [
            {"dimension": "clarity", "description": "第3节中数据同步策略描述模糊"},
            {"dimension": "testability", "description": "缺少具体的性能指标阈值"}
          ],
          "overall": 75
        }
        ```
        """

        with (
            patch("app.engine.diagnosis.quality_evaluator.invoke_llm", return_value=mock_result),
            patch("app.engine.diagnosis.quality_evaluator.assemble_prompt", return_value="system"),
        ):
            from app.engine.diagnosis.quality_evaluator import evaluate_requirement_quality

            result = await evaluate_requirement_quality("需求文档：实现数据同步功能...")

        assert "scores" in result
        assert result["scores"]["completeness"] == 85
        assert result["scores"]["clarity"] == 70
        assert result["scores"]["testability"] == 60
        assert result["scores"]["consistency"] == 90

        assert "issues" in result
        assert len(result["issues"]) == 2

        # overall 应被重新计算为加权分
        # completeness(85)*0.3 + clarity(70)*0.25 + testability(60)*0.25 + consistency(90)*0.2
        # = 25.5 + 17.5 + 15.0 + 18.0 = 76.0
        assert result["overall"] == 76

    async def test_evaluate_quality_no_issues(self):
        """无 issues 时应返回空列表。"""
        mock_result = AsyncMock()
        mock_result.content = """
        {
          "scores": {
            "completeness": 95,
            "clarity": 90,
            "testability": 88,
            "consistency": 92
          },
          "overall": 92
        }
        """

        with (
            patch("app.engine.diagnosis.quality_evaluator.invoke_llm", return_value=mock_result),
            patch("app.engine.diagnosis.quality_evaluator.assemble_prompt", return_value="system"),
        ):
            from app.engine.diagnosis.quality_evaluator import evaluate_requirement_quality

            result = await evaluate_requirement_quality("高质量需求文档...")

        assert result["issues"] == []

    async def test_evaluate_quality_invalid_json(self):
        """LLM 返回无效格式时应抛出 ValueError。"""
        mock_result = AsyncMock()
        mock_result.content = "抱歉，我无法分析这个需求文档。"

        with (
            patch("app.engine.diagnosis.quality_evaluator.invoke_llm", return_value=mock_result),
            patch("app.engine.diagnosis.quality_evaluator.assemble_prompt", return_value="system"),
        ):
            from app.engine.diagnosis.quality_evaluator import evaluate_requirement_quality

            with pytest.raises(ValueError, match="质量评估返回格式异常"):
                await evaluate_requirement_quality("无效输入")
