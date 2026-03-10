"""Tests for API key encryption utilities."""

from app.core.encryption import decrypt_api_key, encrypt_api_key, mask_api_key


class TestEncryptDecrypt:
    def test_roundtrip(self):
        key = "sk-abc123def456xyz789"
        encrypted = encrypt_api_key(key)
        assert encrypted != key
        assert decrypt_api_key(encrypted) == key

    def test_empty_string(self):
        assert encrypt_api_key("") == ""
        assert decrypt_api_key("") == ""

    def test_different_keys_produce_different_ciphertext(self):
        k1 = encrypt_api_key("key-one")
        k2 = encrypt_api_key("key-two")
        assert k1 != k2

    def test_same_key_different_ciphertext(self):
        """Fernet includes a timestamp, so same input produces different output."""
        e1 = encrypt_api_key("same-key")
        e2 = encrypt_api_key("same-key")
        assert e1 != e2
        assert decrypt_api_key(e1) == decrypt_api_key(e2)


class TestMaskApiKey:
    def test_normal_key(self):
        assert mask_api_key("sk-abc123def456xyz789") == "sk-a***z789"

    def test_short_key(self):
        result = mask_api_key("short")
        assert result == "s***t"

    def test_empty(self):
        assert mask_api_key("") == ""

    def test_exact_8_chars(self):
        result = mask_api_key("12345678")
        assert result == "1***8"

    def test_9_chars(self):
        result = mask_api_key("123456789")
        assert result == "1234***6789"
