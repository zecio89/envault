"""Annotations: attach freeform notes/metadata to env keys."""
from __future__ import annotations
import json
from envault.backends.base import BaseBackend


def _annotation_key(env_key: str) -> str:
    return f"__annotations__/{env_key}.json"


def set_annotation(backend: BaseBackend, env_key: str, note: str, author: str = "") -> dict:
    """Attach a note to an env key. Raises KeyError if key doesn't exist."""
    if not backend.exists(env_key):
        raise KeyError(f"Key not found: {env_key}")
    record = {"key": env_key, "note": note, "author": author}
    backend.upload(_annotation_key(env_key), json.dumps(record).encode())
    return record


def get_annotation(backend: BaseBackend, env_key: str) -> dict | None:
    """Return the annotation for a key, or None if not set."""
    ak = _annotation_key(env_key)
    if not backend.exists(ak):
        return None
    return json.loads(backend.download(ak).decode())


def delete_annotation(backend: BaseBackend, env_key: str) -> bool:
    """Delete annotation for a key. Returns True if deleted, False if not found."""
    ak = _annotation_key(env_key)
    if not backend.exists(ak):
        return False
    backend.delete(ak)
    return True


def list_annotations(backend: BaseBackend) -> list[dict]:
    """Return all annotations stored in the backend."""
    results = []
    for k in backend.list_keys():
        if k.startswith("__annotations__/"):
            try:
                results.append(json.loads(backend.download(k).decode()))
            except Exception:
                pass
    return results
