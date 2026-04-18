"""History tracking for env versions in envault."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from envault.backends.base import BaseBackend


def _history_key(env_key: str) -> str:
    return f".history/{env_key}.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def record_version(
    backend: BaseBackend,
    env_key: str,
    encrypted_blob: str,
    actor: str = "unknown",
    note: str = "",
) -> Dict[str, Any]:
    """Append a version entry to the history log for env_key."""
    history = get_history(backend, env_key)
    entry: Dict[str, Any] = {
        "version": len(history) + 1,
        "timestamp": _now_iso(),
        "actor": actor,
        "note": note,
        "blob": encrypted_blob,
    }
    history.append(entry)
    backend.upload(_history_key(env_key), json.dumps(history))
    return entry


def get_history(backend: BaseBackend, env_key: str) -> List[Dict[str, Any]]:
    """Return list of version entries for env_key, oldest first."""
    hk = _history_key(env_key)
    if not backend.exists(hk):
        return []
    return json.loads(backend.download(hk))


def get_latest_version(backend: BaseBackend, env_key: str) -> Optional[Dict[str, Any]]:
    """Return the most recent version entry for env_key, or None if no history exists."""
    history = get_history(backend, env_key)
    return history[-1] if history else None


def restore_version(
    backend: BaseBackend,
    env_key: str,
    version: int,
) -> str:
    """Return the encrypted blob for a specific version number."""
    history = get_history(backend, env_key)
    for entry in history:
        if entry["version"] == version:
            return entry["blob"]
    raise KeyError(f"Version {version} not found for '{env_key}'")


def clear_history(backend: BaseBackend, env_key: str) -> None:
    """Delete the history log for env_key."""
    hk = _history_key(env_key)
    if backend.exists(hk):
        backend.delete(hk)
