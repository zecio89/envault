"""Pin a specific version of an env as the 'stable' reference."""
from __future__ import annotations
import json
from envault.backends.base import BaseBackend

PIN_PREFIX = "__pins__/"


def _pin_key(env_key: str) -> str:
    return f"{PIN_PREFIX}{env_key}.json"


def pin_version(backend: BaseBackend, env_key: str, version_id: str, label: str = "stable") -> dict:
    """Pin env_key at version_id with an optional label."""
    if not backend.exists(env_key):
        raise KeyError(f"Key not found: {env_key}")
    record = {"env_key": env_key, "version_id": version_id, "label": label}
    backend.upload(_pin_key(env_key), json.dumps(record).encode())
    return record


def get_pin(backend: BaseBackend, env_key: str) -> dict | None:
    """Return the pin record for env_key, or None if unpinned."""
    pk = _pin_key(env_key)
    if not backend.exists(pk):
        return None
    return json.loads(backend.download(pk).decode())


def delete_pin(backend: BaseBackend, env_key: str) -> bool:
    """Remove the pin for env_key. Returns True if a pin existed."""
    pk = _pin_key(env_key)
    if not backend.exists(pk):
        return False
    backend.delete(pk)
    return True


def list_pins(backend: BaseBackend) -> list[dict]:
    """Return all pin records stored in the backend."""
    pins = []
    for k in backend.list_keys():
        if k.startswith(PIN_PREFIX) and k.endswith(".json"):
            try:
                pins.append(json.loads(backend.download(k).decode()))
            except Exception:
                pass
    return pins
