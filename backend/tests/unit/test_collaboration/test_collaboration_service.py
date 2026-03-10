"""CollaborationService 回归测试。"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from app.modules.collaboration.service import CollaborationService


def _make_review():
    return SimpleNamespace(
        id=uuid.uuid4(),
        entity_type="requirement",
        entity_id=uuid.uuid4(),
        title="登录测试点评审",
        description="请确认认证主流程覆盖。",
        created_by=uuid.uuid4(),
        status="pending",
        reviewer_ids=[str(uuid.uuid4())],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        deleted_at=None,
    )


def _make_requirement(requirement_id: uuid.UUID):
    return SimpleNamespace(
        id=requirement_id,
        req_id="REQ-LOGIN-001",
        title="用户登录功能需求",
        deleted_at=None,
    )


def _make_scene_map(requirement_id: uuid.UUID):
    return SimpleNamespace(
        id=uuid.uuid4(),
        requirement_id=requirement_id,
        deleted_at=None,
    )


def _make_test_point(scene_map_id: uuid.UUID):
    return SimpleNamespace(
        id=uuid.uuid4(),
        scene_map_id=scene_map_id,
        group_name="认证",
        title="正常登录",
        description="验证合法账号密码登录成功",
        priority="P1",
        status="pending",
        source="document",
        estimated_cases=2,
        sort_order=1,
        created_at=datetime.now(UTC),
        deleted_at=None,
    )


def _make_user(user_id: uuid.UUID):
    return SimpleNamespace(
        id=user_id,
        full_name="张三",
        username="zhangsan",
    )


class TestGetReviewByToken:
    async def test_includes_requirement_snapshot_and_reviewer_names(self):
        """分享评审读取时应补充需求标题、测试点快照与评审人名称。"""
        review = _make_review()
        reviewer_id = uuid.UUID(review.reviewer_ids[0])
        share = SimpleNamespace(review_id=review.id, token="share-token", is_active=True, deleted_at=None)
        requirement = _make_requirement(review.entity_id)
        scene_map = _make_scene_map(review.entity_id)
        test_point = _make_test_point(scene_map.id)
        user = _make_user(reviewer_id)

        share_result = MagicMock()
        share_result.scalar_one_or_none.return_value = share

        scene_map_result = MagicMock()
        scene_map_result.scalar_one_or_none.return_value = scene_map

        test_point_result = MagicMock()
        test_point_result.scalars.return_value.all.return_value = [test_point]

        user_result = MagicMock()
        user_result.scalars.return_value.all.return_value = [user]

        session = AsyncMock()
        session.execute = AsyncMock(
            side_effect=[share_result, scene_map_result, test_point_result, user_result]
        )
        session.get = AsyncMock(return_value=requirement)

        service = CollaborationService(session)
        service.get_review = AsyncMock(return_value=review)
        service._get_decisions = AsyncMock(return_value=[])

        result = await service.get_review_by_token("share-token")

        assert result["review"] == review
        assert result["entity_snapshot"]["requirement_title"] == "用户登录功能需求"
        assert result["entity_snapshot"]["req_id"] == "REQ-LOGIN-001"
        assert result["entity_snapshot"]["test_points"][0]["title"] == "正常登录"
        assert result["entity_snapshot"]["reviewer_names"] == ["张三"]
