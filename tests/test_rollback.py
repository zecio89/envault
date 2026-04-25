"""Tests for envault.rollback."""

from __future__ import annotations

import pytest

from envault.backends.local import LocalBackend
from envault.crypto import decrypt, encrypt
from envault.history import get_history, record_version
from envault.rollback import RollbackResult, rollback_env


PASS = "hunter2"
KEY = "production"


@pytest.fixture()
def backend(tmp_path):
    return LocalBackend(str(tmp_path))


@pytest.fixture()
def populated_backend(backend):
    """Backend with KEY having two recorded versions."""
    blob_v1 = encrypt("FOO=bar\nBAZ=qux\n", PASS)
    backend.upload(KEY, blob_v1)
    record_version(backend, KEY, blob_v1, PASS)

    blob_v2 = encrypt("FOO=updated\nBAZ=qux\n", PASS)
    backend.upload(KEY, blob_v2)
    record_version(backend, KEY, blob_v2, PASS)

    return backend


def _first_version_id(backend, key: str) -> str:
    return get_history(backend, key)[0]["version_id"]


def _latest_version_id(backend, key: str) -> str:
    return get_history(backend, key)[-1]["version_id"]


# ---------------------------------------------------------------------------
# Basic contract
# ---------------------------------------------------------------------------

def test_rollback_returns_result(populated_backend):
    vid = _first_version_id(populated_backend, KEY)
    result = rollback_env(populated_backend, KEY, vid, PASS)
    assert isinstance(result, RollbackResult)
    assert result.key == KEY
    assert result.rolled_back_to == vid


def test_rollback_restores_content(populated_backend):
    vid = _first_version_id(populated_backend, KEY)
    result = rollback_env(populated_backend, KEY, vid, PASS)
    plaintext = decrypt(result.blob, PASS)
    assert "FOO=bar" in plaintext


def test_rollback_updates_backend(populated_backend):
    vid = _first_version_id(populated_backend, KEY)
    rollback_env(populated_backend, KEY, vid, PASS)
    stored = populated_backend.download(KEY)
    assert decrypt(stored, PASS).startswith("FOO=bar")


def test_rollback_records_new_history_entry(populated_backend):
    before_count = len(get_history(populated_backend, KEY))
    vid = _first_version_id(populated_backend, KEY)
    rollback_env(populated_backend, KEY, vid, PASS)
    after_count = len(get_history(populated_backend, KEY))
    assert after_count == before_count + 1


def test_rollback_previous_version_is_set(populated_backend):
    latest = _latest_version_id(populated_backend, KEY)
    vid = _first_version_id(populated_backend, KEY)
    result = rollback_env(populated_backend, KEY, vid, PASS)
    assert result.previous_version == latest


# ---------------------------------------------------------------------------
# Re-encryption
# ---------------------------------------------------------------------------

def test_rollback_reencrypt_with_new_passphrase(populated_backend):
    new_pass = "newpass123"
    vid = _first_version_id(populated_backend, KEY)
    result = rollback_env(populated_backend, KEY, vid, PASS, new_passphrase=new_pass)
    plaintext = decrypt(result.blob, new_pass)
    assert "FOO=bar" in plaintext


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------

def test_rollback_missing_key_raises(backend):
    with pytest.raises(KeyError, match="not found in backend"):
        rollback_env(backend, "nonexistent", "v1", PASS)


def test_rollback_missing_version_raises(populated_backend):
    with pytest.raises(KeyError, match="not found in history"):
        rollback_env(populated_backend, KEY, "bogus-version-id", PASS)


def test_rollback_wrong_passphrase_raises(populated_backend):
    vid = _first_version_id(populated_backend, KEY)
    with pytest.raises(Exception):
        rollback_env(populated_backend, KEY, vid, "wrongpassphrase")
