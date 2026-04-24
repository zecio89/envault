"""Expiry management for env keys — set TTLs and detect expired entries."""

from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from typing import Optional

from envault.backends.base import BaseBackend


def _expiry_key(env_key: str) -> str:
    return f"__expiry__/{env_key}.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def set_expiry(backend: BaseBackend, env_key: str, ttl_days: int) -> dict:
    """Record an expiry TTL (in days) for *env_key*.

    Raises KeyError if the env key does not exist in the backend.
    Raises ValueError if ttl_days is not a positive integer.
    """
    if not backend.exists(env_key):
        raise KeyError(f"Key not found in backend: {env_key!r}")
    if ttl_days <= 0:
        raise ValueError(f"ttl_days must be a positive integer, got {ttl_days}")

    expires_at = (
        datetime.now(timezone.utc) + timedelta(days=ttl_days)
    ).isoformat()

    record = {
        "env_key": env_key,
        "ttl_days": ttl_days,
        "set_at": _now_iso(),
        "expires_at": expires_at,
    }
    backend.upload(_expiry_key(env_key), json.dumps(record).encode())
    return record


def get_expiry(backend: BaseBackend, env_key: str) -> Optional[dict]:
    """Return the expiry record for *env_key*, or None if none is set."""
    key = _expiry_key(env_key)
    if not backend.exists(key):
        return None
    return json.loads(backend.download(key).decode())


def delete_expiry(backend: BaseBackend, env_key: str) -> bool:
    """Remove the expiry record for *env_key*. Returns True if deleted."""
    key = _expiry_key(env_key)
    if not backend.exists(key):
        return False
    backend.delete(key)
    return True


def is_expired(backend: BaseBackend, env_key: str) -> bool:
    """Return True if *env_key* has an expiry record that is past due."""
    record = get_expiry(backend, env_key)
    if record is None:
        return False
    expires_at = datetime.fromisoformat(record["expires_at"])
    return datetime.now(timezone.utc) >= expires_at


def list_expiring(backend: BaseBackend, within_days: int = 0) -> list[dict]:
    """Return expiry records for all keys expiring within *within_days* days.

    If *within_days* is 0 (default) only already-expired keys are returned.
    """
    cutoff = datetime.now(timezone.utc) + timedelta(days=within_days)
    results = []
    for raw_key in backend.list_keys():
        if not raw_key.startswith("__expiry__/"):
            continue
        record = json.loads(backend.download(raw_key).decode())
        expires_at = datetime.fromisoformat(record["expires_at"])
        if expires_at <= cutoff:
            results.append(record)
    results.sort(key=lambda r: r["expires_at"])
    return results
