from datetime import UTC, datetime
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.core.security import get_password_hash
from app.modules.auth.models import User
from app.modules.auth.schemas import UserCreate
from app.modules.auth.service import AuthService


@pytest.mark.asyncio
async def test_register_rejects_passwords_over_72_bytes() -> None:
    """注册时应将 bcrypt 密码长度限制转换为 400 错误。"""
    service = AuthService(AsyncMock())
    payload = UserCreate(
        email="tester@example.com",
        username="tester",
        password="a" * 73,
        full_name="Tester",
    )

    with pytest.raises(HTTPException, match="72 bytes") as exc_info:
        await service.register(payload)

    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_authenticate_returns_token_with_user_profile() -> None:
    """登录响应应携带 token 与当前用户信息，供前端持久化会话。"""
    session = AsyncMock()
    user = User(
        email="tester@example.com",
        username="tester",
        hashed_password=get_password_hash("Password123!"),
        full_name="Tester",
        role="admin",
    )
    user.id = uuid.uuid4()
    user.created_at = datetime.now(UTC)
    user.updated_at = datetime.now(UTC)
    user.is_active = True

    result = MagicMock()
    result.scalar_one_or_none.return_value = user
    session.execute.return_value = result

    service = AuthService(session)
    token = await service.authenticate("tester", "Password123!")

    assert token is not None
    assert token.access_token
    assert token.user.id == user.id
    assert token.user.username == "tester"
    assert token.user.email == "tester@example.com"


@pytest.mark.asyncio
async def test_authenticate_returns_none_for_soft_deleted_user() -> None:
    """软删除用户即使处于激活状态，也不应再签发登录 token。"""
    session = AsyncMock()
    user = User(
        email="deleted@example.com",
        username="deleted-user",
        hashed_password=get_password_hash("Password123!"),
        full_name="Deleted User",
        role="tester",
    )
    user.id = uuid.uuid4()
    user.created_at = datetime.now(UTC)
    user.updated_at = datetime.now(UTC)
    user.deleted_at = datetime.now(UTC)
    user.is_active = True

    result = MagicMock()
    result.scalar_one_or_none.return_value = user
    session.execute.return_value = result

    service = AuthService(session)

    token = await service.authenticate("deleted-user", "Password123!")

    assert token is None


@pytest.mark.asyncio
async def test_get_by_id_returns_none_for_soft_deleted_user() -> None:
    """get_by_id 不应返回软删除用户。"""
    session = AsyncMock()
    user = User(
        email="deleted@example.com",
        username="deleted-user",
        hashed_password=get_password_hash("Password123!"),
        full_name="Deleted User",
        role="tester",
    )
    user.id = uuid.uuid4()
    user.created_at = datetime.now(UTC)
    user.updated_at = datetime.now(UTC)
    user.deleted_at = datetime.now(UTC)

    session.get.return_value = user

    service = AuthService(session)

    result = await service.get_by_id(user.id)

    assert result is None
