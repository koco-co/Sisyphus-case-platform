"""B-M03-07 — 深度追问器单元测试"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest


class TestGenerateQuestions:
    """测试基于风险摘要生成追问问题。"""

    async def test_generate_followup_question(self):
        """应基于风险摘要生成针对性追问。"""
        mock_result = AsyncMock()
        mock_result.content = "请问数据同步任务在源端数据库连接中断时，系统如何处理已拉取的部分数据？"

        with (
            patch("app.engine.diagnosis.questioner.invoke_llm", return_value=mock_result),
            patch("app.engine.diagnosis.questioner.assemble_prompt", return_value="system prompt"),
        ):
            from app.engine.diagnosis.questioner import generate_followup_question

            result = await generate_followup_question(
                risk_summary="- [HIGH] 数据同步中断恢复: 未描述中断后的数据一致性保障",
                history=[],
                round_num=1,
            )

        assert isinstance(result, str)
        assert len(result) > 0

    async def test_generate_with_history(self):
        """有历史对话时应包含上下文。"""
        mock_result = AsyncMock()
        mock_result.content = "那么在并发同步场景下，锁机制如何避免死锁？"

        with (
            patch("app.engine.diagnosis.questioner.invoke_llm", return_value=mock_result) as mock_llm,
            patch("app.engine.diagnosis.questioner.assemble_prompt", return_value="system prompt"),
        ):
            from app.engine.diagnosis.questioner import generate_followup_question

            history = [
                {"role": "assistant", "content": "请问同步任务失败后如何重试？"},
                {"role": "user", "content": "我们使用指数退避重试，最多3次"},
            ]
            result = await generate_followup_question(
                risk_summary="- [MEDIUM] 并发同步: 未描述锁机制",
                history=history,
                round_num=2,
            )

        assert isinstance(result, str)
        mock_llm.assert_awaited_once()


class TestShouldContinueQuestioning:
    """测试追问终止条件判断。"""

    def test_continue_within_limit(self):
        from app.engine.diagnosis.questioner import should_continue_questioning

        assert should_continue_questioning(1, "关于边界值的处理...") is True
        assert should_continue_questioning(2, "关于异常处理...") is True

    def test_stop_at_max_rounds(self):
        from app.engine.diagnosis.questioner import should_continue_questioning

        assert should_continue_questioning(3, "继续追问") is False

    def test_stop_on_summary(self):
        from app.engine.diagnosis.questioner import should_continue_questioning

        assert should_continue_questioning(1, "**📋 追问总结**\n1. 已确认...") is False


class TestBuildRiskSummary:
    """测试风险摘要构建。"""

    def test_build_risk_summary(self):
        from app.engine.diagnosis.questioner import build_risk_summary

        risks = [
            {"risk_level": "high", "title": "数据丢失", "description": "未描述断点续传"},
            {"level": "medium", "title": "性能瓶颈", "description": "大数据量未做分页"},
        ]
        result = build_risk_summary(risks)

        assert "[HIGH]" in result
        assert "数据丢失" in result
        assert "[MEDIUM]" in result
        assert "性能瓶颈" in result

    def test_build_risk_summary_empty(self):
        from app.engine.diagnosis.questioner import build_risk_summary

        result = build_risk_summary([])
        assert "暂未发现" in result
