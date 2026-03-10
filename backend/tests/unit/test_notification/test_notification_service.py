from __future__ import annotations

import uuid
from unittest.mock import AsyncMock

import pytest

from app.modules.notification.service import NotificationService


@pytest.mark.asyncio
async def test_soft_delete_marks_notification_deleted() -> None:
    """删除通知应走软删除并提交事务。"""
    session = AsyncMock()
    notification = AsyncMock()
    notification.deleted_at = None
    session.get.return_value = notification

    service = NotificationService(session)
    deleted = await service.soft_delete(notification_id=uuid.uuid4())

    assert deleted is True
    assert notification.deleted_at is not None
    session.commit.assert_awaited_once()
