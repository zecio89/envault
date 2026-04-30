"""Tests for envault.sign."""
from __future__ import annotations

import json
import pytest

from envault.backends.local import LocalBackend
from envault.sign import (
    _sig_key,
    delete_signature,
    get_signature,
    list_signed,
    sign_env,
    verify_signature,
)

SECRET = "test-hmac-secret"


@pytest.fixture()
def backend(tmp_path):
    b = LocalBackend(root=str(tmp_path))
    b.upload("production", b"ENCRYPTED_BLOB_DATA")
    b.upload("staging", b"ANOTHER_BLOB")
    return b


def test_sign_env_returns_record(backend):
    record = sign_env(backend, "production", SECRET)
    assert record["env_key"] == "production"
    assert record["algorithm"] == "hmac-sha256"
    assert isinstance(record["digest"], str)
    assert len(record["digest"]) == 64  # SHA-256 hex


def test_sign_env_stored_in_backend(backend):
    sign_env(backend, "production", SECRET)
    sig_key = _sig_key("production")
    assert backend.exists(sig_key)
    stored = json.loads(backend.download(sig_key).decode())
    assert stored["env_key"] == "production"


def test_sign_env_missing_key_raises(backend):
    with pytest.raises(KeyError, match="missing"):
        sign_env(backend, "missing", SECRET)


def test_get_signature_returns_record(backend):
    sign_env(backend, "production", SECRET)
    record = get_signature(backend, "production")
    assert record is not None
    assert record["env_key"] == "production"


def test_get_signature_returns_none_when_unsigned(backend):
    assert get_signature(backend, "staging") is None


def test_verify_signature_valid(backend):
    sign_env(backend, "production", SECRET)
    assert verify_signature(backend, "production", SECRET) is True


def test_verify_signature_wrong_secret(backend):
    sign_env(backend, "production", SECRET)
    assert verify_signature(backend, "production", "wrong-secret") is False


def test_verify_signature_no_sig_returns_false(backend):
    assert verify_signature(backend, "staging", SECRET) is False


def test_verify_signature_missing_key_raises(backend):
    with pytest.raises(KeyError):
        verify_signature(backend, "nonexistent", SECRET)


def test_verify_detects_tampered_blob(backend):
    sign_env(backend, "production", SECRET)
    # Tamper with the blob after signing
    backend.upload("production", b"TAMPERED_DATA")
    assert verify_signature(backend, "production", SECRET) is False


def test_delete_signature_returns_true_when_exists(backend):
    sign_env(backend, "production", SECRET)
    assert delete_signature(backend, "production") is True
    assert get_signature(backend, "production") is None


def test_delete_signature_returns_false_when_none(backend):
    assert delete_signature(backend, "staging") is False


def test_list_signed_returns_keys(backend):
    sign_env(backend, "production", SECRET)
    sign_env(backend, "staging", SECRET)
    signed = list_signed(backend)
    assert set(signed) == {"production", "staging"}


def test_list_signed_empty_when_none(backend):
    assert list_signed(backend) == []
