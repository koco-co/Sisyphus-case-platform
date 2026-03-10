import pytest

from app.core.security import get_password_hash, verify_password


def test_get_password_hash_and_verify_password_round_trip() -> None:
    """短密码应可以正常哈希并通过校验。"""
    password = "Password123!"

    hashed = get_password_hash(password)

    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword123!", hashed) is False


def test_get_password_hash_rejects_passwords_over_72_bytes() -> None:
    """超过 bcrypt 限制的密码应被显式拒绝。"""
    with pytest.raises(ValueError, match="72 bytes"):
        get_password_hash("a" * 73)
