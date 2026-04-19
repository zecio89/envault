"""Tests for envault.rename."""
from __future__ import annotations

import pytest

from envault.backends.local import LocalBackend
from envault.crypto import encrypt
from envault.rename import rename_env

PASSPHRASE = "test-secret"


@pytest.fixture()
def backend(tmp_path):
    return LocalBackend(root=str(tmp_path))


@pytest.fixture()
def populated_backend(backend):
    blob = encrypt("KEY=value", PASSPHRASE)
    backend.upload("prod", blob.encode())
    return backend


def test_rename_returns_dict(populated_backend):
    result = rename_env(populated_backend, "prod", "production", PASSPHRASE)
    assert result == {"old_key": "prod", "new_key": "production"}


def test_rename_new_key_exists(populated_backend):
    populated_backend.upload("production", b"blob")
    with pytest.raises(ValueError, match="already exists"):
        rename_env(populated_backend, "prod", "production", PASSPHRASE)


def test_rename_old_key_missing(populated_backend):
    with pytest.raises(KeyError, match="not found"):
        rename_env(populated_backend, "missing", "other", PASSPHRASE)


def test_rename_old_key_removed(populated_backend):
    rename_env(populated_backend, "prod", "production", PASSPHRASE)
    assert not populated_backend.exists("prod")


def test_rename_new_key_present(populated_backend):
    rename_env(populated_backend, "prod", "production", PASSPHRASE)
    assert populated_backend.exists("production")


def test_rename_blob_preserved(populated_backend):
    original_blob = populated_backend.download("prod")
    rename_env(populated_backend, "prod", "production", PASSPHRASE)
    assert populated_backend.download("production") == original_blob
