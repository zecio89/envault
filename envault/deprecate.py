"""Mark env keys as deprecated with optional replacement and sunset date."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Optional

from envault.backends.base import BaseBackend


def _deprecation_key(env_key: str) -> str:
    return f"__deprecations__/{env_key}.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def mark_deprecated(
    backend: BaseBackend,
    env_key: str,
    reason: str,
    replacement: Optional[str] = None,
    sunset: Optional[str] = None,
) -> dict:
    """Mark an env key as deprecated.

    Args:
        backend: Storage backend.
        env_key: The key to deprecate.
        reason: Human-readable reason for deprecation.
        replacement: Optional key that should be used instead.
        sunset: Optional ISO date string after which the key will be removed.

    Returns:
        The deprecation record as a dict.

    Raises:
        KeyError: If env_key does not exist in the backend.
    """
    if not backend.exists(env_key):
        raise KeyError(f"Key not found: {env_key!r}")

    record = {
        "key": env_key,
        "reason": reason,
        "replacement": replacement,
        "sunset": sunset,
        "deprecated_at": _now_iso(),
    }
    backend.upload(_deprecation_key(env_key), json.dumps(record).encode())
    return record


def get_deprecation(backend: BaseBackend, env_key: str) -> Optional[dict]:
    """Return the deprecation record for env_key, or None if not deprecated."""
    dkey = _deprecation_key(env_key)
    if not backend.exists(dkey):
        return None
    return json.loads(backend.download(dkey).decode())


def clear_deprecation(backend: BaseBackend, env_key: str) -> bool:
    """Remove the deprecation marker for env_key.

    Returns True if a marker was removed, False if none existed.
    """
    dkey = _deprecation_key(env_key)
    if not backend.exists(dkey):
        return False
    backend.delete(dkey)
    return True


def list_deprecated(backend: BaseBackend) -> list[dict]:
    """Return all deprecation records stored in the backend."""
    prefix = "__deprecations__/"
    records = []
    for key in backend.list_keys():
        if key.startswith(prefix) and key.endswith(".json"):
            try:
                records.append(json.loads(backend.download(key).decode()))
            except Exception:
                pass
    return records


def is_sunset(record: dict) -> bool:
    """Return True if the sunset date has passed (or equals today)."""
    if not record.get("sunset"):
        return False
    sunset_dt = datetime.fromisoformat(record["sunset"])
    if sunset_dt.tzinfo is None:
        sunset_dt = sunset_dt.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) >= sunset_dt
