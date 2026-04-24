"""Tests for envault.expiry."""

from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

from envault.backends.local import LocalBackend
from envault.expiry import (
    set_expiry,
    get_expiry,
    delete_expiry,
    is_expired,
    list_expiring,
)


@pytest.fixture()
def backend(tmp_path: Path) -> LocalBackend:
    b = LocalBackend(root=str(tmp_path))
    # Pre-populate two env keys so expiry can reference them.
    b.upload("staging", b"encrypted-blob-staging")
    b.upload("production", b"encrypted-blob-production")
    return b


def test_set_expiry_returns_record(backend):
    record = set_expiry(backend, "staging", ttl_days=30)
    assert record["env_key"] == "staging"
    assert record["ttl_days"] == 30
    assert "expires_at" in record
    assert "set_at" in record


def test_set_expiry_stored_in_backend(backend):
    set_expiry(backend, "staging", ttl_days=7)
    assert backend.exists("__expiry__/staging.json")


def test_set_expiry_raises_for_missing_key(backend):
    with pytest.raises(KeyError, match="missing-key"):
        set_expiry(backend, "missing-key", ttl_days=10)


def test_set_expiry_raises_for_invalid_ttl(backend):
    with pytest.raises(ValueError):
        set_expiry(backend, "staging", ttl_days=0)
    with pytest.raises(ValueError):
        set_expiry(backend, "staging", ttl_days=-5)


def test_get_expiry_returns_record(backend):
    set_expiry(backend, "staging", ttl_days=14)
    record = get_expiry(backend, "staging")
    assert record is not None
    assert record["ttl_days"] == 14


def test_get_expiry_returns_none_when_unset(backend):
    assert get_expiry(backend, "staging") is None


def test_delete_expiry_removes_record(backend):
    set_expiry(backend, "staging", ttl_days=5)
    result = delete_expiry(backend, "staging")
    assert result is True
    assert get_expiry(backend, "staging") is None


def test_delete_expiry_returns_false_when_none(backend):
    assert delete_expiry(backend, "staging") is False


def test_is_expired_false_for_future(backend):
    set_expiry(backend, "staging", ttl_days=365)
    assert is_expired(backend, "staging") is False


def test_is_expired_true_for_past(backend, tmp_path):
    # Manually write a record with an already-past expiry.
    past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    record = {"env_key": "staging", "ttl_days": 1, "set_at": past, "expires_at": past}
    backend.upload("__expiry__/staging.json", json.dumps(record).encode())
    assert is_expired(backend, "staging") is True


def test_is_expired_false_when_no_expiry(backend):
    assert is_expired(backend, "staging") is False


def test_list_expiring_returns_expired(backend):
    past = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
    record = {"env_key": "staging", "ttl_days": 1, "set_at": past, "expires_at": past}
    backend.upload("__expiry__/staging.json", json.dumps(record).encode())
    set_expiry(backend, "production", ttl_days=999)
    results = list_expiring(backend, within_days=0)
    keys = [r["env_key"] for r in results]
    assert "staging" in keys
    assert "production" not in keys


def test_list_expiring_within_days(backend):
    set_expiry(backend, "staging", ttl_days=3)
    set_expiry(backend, "production", ttl_days=999)
    results = list_expiring(backend, within_days=7)
    keys = [r["env_key"] for r in results]
    assert "staging" in keys
    assert "production" not in keys
