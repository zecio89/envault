"""Rotation reminders: track when an env was last rotated and warn if overdue."""

import json
from datetime import datetime, timezone
from envault.backends.base import BaseBackend

_REMINDER_PREFIX = "__reminders__/"


def _reminder_key(env_key: str) -> str:
    return f"{_REMINDER_PREFIX}{env_key}.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def record_rotation(backend: BaseBackend, env_key: str) -> dict:
    """Record the current time as the last rotation time for env_key."""
    if not backend.exists(env_key):
        raise KeyError(f"Key not found: {env_key}")
    entry = {"env_key": env_key, "last_rotated": _now_iso()}
    backend.upload(_reminder_key(env_key), json.dumps(entry).encode())
    return entry


def get_rotation_info(backend: BaseBackend, env_key: str) -> dict | None:
    """Return rotation info for env_key, or None if never recorded."""
    rk = _reminder_key(env_key)
    if not backend.exists(rk):
        return None
    return json.loads(backend.download(rk).decode())


def check_overdue(backend: BaseBackend, env_key: str, max_days: int = 30) -> bool:
    """Return True if env_key has not been rotated within max_days."""
    info = get_rotation_info(backend, env_key)
    if info is None:
        return True
    last = datetime.fromisoformat(info["last_rotated"])
    now = datetime.now(timezone.utc)
    return (now - last).days >= max_days


def list_overdue(backend: BaseBackend, max_days: int = 30) -> list[str]:
    """Return list of env keys that are overdue for rotation."""
    all_keys = [k for k in backend.list_keys() if not k.startswith("__")]
    return [k for k in all_keys if check_overdue(backend, k, max_days)]


def delete_reminder(backend: BaseBackend, env_key: str) -> None:
    """Remove rotation reminder record for env_key."""
    rk = _reminder_key(env_key)
    if backend.exists(rk):
        backend.delete(rk)
