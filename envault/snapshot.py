"""Snapshot: capture and restore full environment snapshots (all keys at once)."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from typing import Optional

from envault.backends.base import BaseBackend
from envault.crypto import encrypt, decrypt


def _snapshot_key(name: str) -> str:
    return f"__snapshots__/{name}.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_snapshot(backend: BaseBackend, passphrase: str, name: Optional[str] = None) -> dict:
    """Encrypt all current env blobs into a single snapshot."""
    keys = [k for k in backend.list_keys() if not k.startswith("__")]
    if not keys:
        raise ValueError("No environment keys found to snapshot.")

    name = name or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    blobs = {k: backend.download(k).decode() for k in keys}
    payload = json.dumps({"created_at": _now_iso(), "keys": blobs})
    encrypted = encrypt(payload, passphrase)
    backend.upload(_snapshot_key(name), encrypted.encode())
    return {"name": name, "key_count": len(keys), "created_at": _now_iso()}


def list_snapshots(backend: BaseBackend) -> list[str]:
    return [
        k[len("__snapshots__/"):-5]
        for k in backend.list_keys()
        if k.startswith("__snapshots__/") and k.endswith(".json")
    ]


def restore_snapshot(backend: BaseBackend, name: str, passphrase: str) -> list[str]:
    """Restore all keys from a snapshot, overwriting current values."""
    raw = backend.download(_snapshot_key(name))
    payload = decrypt(raw.decode(), passphrase)
    data = json.loads(payload)
    for key, blob in data["keys"].items():
        backend.upload(key, blob.encode())
    return list(data["keys"].keys())


def delete_snapshot(backend: BaseBackend, name: str) -> None:
    key = _snapshot_key(name)
    if not backend.exists(key):
        raise KeyError(f"Snapshot '{name}' not found.")
    backend.delete(key)
