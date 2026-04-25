"""Tests for envault.prune."""

from __future__ import annotations

import pytest
from datetime import datetime, timezone, timedelta

from envault.backends.local import LocalBackend
from envault.expiry import set_expiry
from envault.crypto import encrypt
from envault.prune import prune_expired, PruneResult


PASS = "test-pass"


@pytest.fixture()
def backend(tmp_path):
    return LocalBackend(str(tmp_path))


def _store(backend, key: str, value: str = "VAL=1") -> None:
    backend.upload(key, encrypt(value, PASS))


def _past_iso(days: int = 1) -> str:
    dt = datetime.now(timezone.utc) - timedelta(days=days)
    return dt.isoformat()


def _future_iso(days: int = 1) -> str:
    dt = datetime.now(timezone.utc) + timedelta(days=days)
    return dt.isoformat()


@pytest.fixture()
def populated_backend(backend):
    _store(backend, "expired-env")
    set_expiry(backend, "expired-env", ttl_days=1)
    # Manually overwrite the expiry to be in the past
    import json
    expiry_key = f"__expiry__expired-env"
    record = json.loads(backend.download(expiry_key))
    record["expires_at"] = _past_iso(2)
    backend.upload(expiry_key, json.dumps(record))

    _store(backend, "active-env")
    set_expiry(backend, "active-env", ttl_days=30)

    _store(backend, "no-expiry-env")
    return backend


def test_prune_returns_prune_result(populated_backend):
    result = prune_expired(populated_backend)
    assert isinstance(result, PruneResult)


def test_prune_removes_expired_key(populated_backend):
    result = prune_expired(populated_backend)
    assert "expired-env" in result.pruned
    assert not populated_backend.exists("expired-env")


def test_prune_skips_active_key(populated_backend):
    result = prune_expired(populated_backend)
    assert "active-env" in result.skipped
    assert populated_backend.exists("active-env")


def test_prune_skips_key_without_expiry(populated_backend):
    result = prune_expired(populated_backend)
    assert "no-expiry-env" in result.skipped


def test_prune_dry_run_does_not_delete(populated_backend):
    result = prune_expired(populated_backend, dry_run=True)
    assert "expired-env" in result.pruned
    # Key must still exist because dry_run=True
    assert populated_backend.exists("expired-env")


def test_prune_explicit_keys(populated_backend):
    result = prune_expired(populated_backend, keys=["active-env"])
    assert "active-env" in result.skipped
    assert result.total_pruned == 0


def test_prune_all_ok_when_no_errors(populated_backend):
    result = prune_expired(populated_backend)
    assert result.all_ok


def test_prune_empty_backend(backend):
    result = prune_expired(backend)
    assert result.total_pruned == 0
    assert result.all_ok
