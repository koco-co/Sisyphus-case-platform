"""API Key 加密工具 — Fernet 对称加密 + 密钥掩码显示。"""

from __future__ import annotations

import base64
import hashlib
import logging
import os

from cryptography.fernet import Fernet

from app.core.config import settings

logger = logging.getLogger(__name__)


def _get_fernet() -> Fernet:
    """Get Fernet instance using SECRET_KEY as basis for encryption key.

    Derives a valid Fernet key from the application secret using SHA-256.
    """
    secret = getattr(settings, "secret_key", None) or os.environ.get("SECRET_KEY", "sisyphus-default-key")
    key = base64.urlsafe_b64encode(hashlib.sha256(secret.encode()).digest())
    return Fernet(key)


def encrypt_api_key(plain_key: str) -> str:
    """Encrypt an API key for storage.

    Args:
        plain_key: The plaintext API key

    Returns:
        Encrypted string (base64-encoded Fernet token)
    """
    if not plain_key:
        return ""
    fernet = _get_fernet()
    return fernet.encrypt(plain_key.encode()).decode()


def decrypt_api_key(encrypted_key: str) -> str:
    """Decrypt a stored API key.

    Args:
        encrypted_key: The encrypted API key string

    Returns:
        Decrypted plaintext key
    """
    if not encrypted_key:
        return ""
    fernet = _get_fernet()
    return fernet.decrypt(encrypted_key.encode()).decode()


def mask_api_key(plain_key: str) -> str:
    """Mask an API key for display, showing only first 4 and last 4 chars.

    Examples:
        'sk-abc123def456xyz789' → 'sk-a***z789'
        'short' → 's***t'
        '' → ''
    """
    if not plain_key:
        return ""
    if len(plain_key) <= 8:
        return plain_key[0] + "***" + plain_key[-1]
    return plain_key[:4] + "***" + plain_key[-4:]
