"""Tests for envault.crypto encryption/decryption utilities."""

import pytest
from envault.crypto import encrypt, decrypt


PASSPHRASE = "super-secret-passphrase"
PLAINTEXT = "DB_PASSWORD=hunter2\nAPI_KEY=abc123\n"


def test_encrypt_returns_string():
    token = encrypt(PLAINTEXT, PASSPHRASE)
    assert isinstance(token, str)
    assert len(token) > 0


def test_encrypt_produces_unique_ciphertexts():
    """Each call should produce a different ciphertext due to random salt/nonce."""
    token1 = encrypt(PLAINTEXT, PASSPHRASE)
    token2 = encrypt(PLAINTEXT, PASSPHRASE)
    assert token1 != token2


def test_decrypt_roundtrip():
    token = encrypt(PLAINTEXT, PASSPHRASE)
    result = decrypt(token, PASSPHRASE)
    assert result == PLAINTEXT


def test_decrypt_wrong_passphrase_raises():
    token = encrypt(PLAINTEXT, PASSPHRASE)
    with pytest.raises(ValueError, match="Decryption failed"):
        decrypt(token, "wrong-passphrase")


def test_decrypt_invalid_base64_raises():
    with pytest.raises(ValueError, match="Invalid base64 payload"):
        decrypt("!!!not-base64!!!", PASSPHRASE)


def test_decrypt_truncated_payload_raises():
    with pytest.raises(ValueError, match="Payload too short"):
        import base64
        short = base64.b64encode(b"tooshort").decode()
        decrypt(short, PASSPHRASE)


def test_encrypt_empty_string():
    token = encrypt("", PASSPHRASE)
    assert decrypt(token, PASSPHRASE) == ""


def test_encrypt_unicode_content():
    content = "SECRET=caf\u00e9\nNAME=\u4e2d\u6587\n"
    token = encrypt(content, PASSPHRASE)
    assert decrypt(token, PASSPHRASE) == content
