from datetime import UTC, datetime, timedelta

import bcrypt
from jose import jwt

from app.core.config import settings

MAX_BCRYPT_PASSWORD_BYTES = 72


def _encode_password(password: str) -> bytes:
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > MAX_BCRYPT_PASSWORD_BYTES:
        raise ValueError(
            f"Password cannot be longer than {MAX_BCRYPT_PASSWORD_BYTES} bytes for bcrypt hashing"
        )
    return password_bytes


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        password_bytes = _encode_password(plain_password)
    except ValueError:
        return False
    return bcrypt.checkpw(password_bytes, hashed_password.encode("utf-8"))


def get_password_hash(password: str) -> str:
    password_bytes = _encode_password(password)
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode("utf-8")


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    expire = datetime.now(UTC) + (expires_delta or timedelta(minutes=settings.jwt_access_token_expire_minutes))
    to_encode = {"sub": subject, "exp": expire}
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
