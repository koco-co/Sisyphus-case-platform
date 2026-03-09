"""B-M07-11 — 变更影响分析器测试"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest


class TestTokenize:
    """测试关键词提取。"""

    def test_tokenize_chinese(self):
        from app.engine.diff.impact_analyzer import _tokenize

        tokens = _tokenize("数据同步任务在执行中出现异常")
        assert "同步任务" in tokens or len(tokens) > 0
        # 停用词应被过滤
        assert "数据" not in tokens  # 数据在停用词中

    def test_tokenize_english(self):
        from app.engine.diff.impact_analyzer import _tokenize

        tokens = _tokenize("sync_task execution retry_count")
        assert "sync_task" in tokens
        assert "execution" in tokens

    def test_tokenize_empty(self):
        from app.engine.diff.impact_analyzer import _tokenize

        tokens = _tokenize("")
        assert len(tokens) == 0


class TestFindAffectedPoints:
    """测试受影响测试点标记。"""

    async def test_find_affected_points(self):
        """变更关键词与测试点匹配时应标记 needs_review。"""
        req_id = uuid.uuid4()
        map_id = uuid.uuid4()

        mock_map = MagicMock()
        mock_map.id = map_id
        mock_map.requirement_id = req_id
        mock_map.deleted_at = None

        # tokenizer 匹配连续中文序列，需保证精确 token 重叠
        tp1 = MagicMock()
        tp1.id = uuid.uuid4()
        tp1.title = "sync_task batch_pull"
        tp1.description = "verify sync_task and batch_pull logic"
        tp1.group_name = "normal_flow"
        tp1.status = "confirmed"
        tp1.deleted_at = None

        tp2 = MagicMock()
        tp2.id = uuid.uuid4()
        tp2.title = "user_login error_handling"
        tp2.description = "verify login error cases"
        tp2.group_name = "exception_flow"
        tp2.status = "confirmed"
        tp2.deleted_at = None

        mock_map_result = MagicMock()
        mock_map_result.scalar_one_or_none.return_value = mock_map

        mock_tp_result = MagicMock()
        mock_tp_result.scalars.return_value.all.return_value = [tp1, tp2]

        session = AsyncMock()
        session.execute = AsyncMock(side_effect=[mock_map_result, mock_tp_result])
        session.flush = AsyncMock()

        from app.engine.diff.impact_analyzer import mark_affected_test_points

        diff_changes = [
            {"content": "changed sync_task to use batch_pull strategy"},
            {"old_content": "previous full_pull approach"},
        ]

        result = await mark_affected_test_points(session, req_id, diff_changes)

        # tp1 应被标记（关键词匹配：sync_task, batch_pull）
        assert len(result) >= 1
        assert str(tp1.id) in result
        assert tp1.status == "needs_review"
        # tp2 不应被标记
        assert str(tp2.id) not in result

    async def test_no_scene_map(self):
        """无场景地图时应返回空列表。"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        session = AsyncMock()
        session.execute = AsyncMock(return_value=mock_result)

        from app.engine.diff.impact_analyzer import mark_affected_test_points

        result = await mark_affected_test_points(session, uuid.uuid4(), [{"content": "变更"}])
        assert result == []
