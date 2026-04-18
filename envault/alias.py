"""Alias support: map friendly names to env keys."""

import json
from envault.backends.base import BaseBackend

_ALIAS_KEY = "__aliases__.json"


def _load(backend: BaseBackend) -> dict:
    if not backend.exists(_ALIAS_KEY):
        return {}
    return json.loads(backend.download(_ALIAS_KEY))


def _save(backend: BaseBackend, data: dict) -> None:
    backend.upload(_ALIAS_KEY, json.dumps(data, indent=2).encode())


def set_alias(backend: BaseBackend, alias: str, key: str) -> dict:
    """Map alias -> key. key must exist in backend."""
    if not backend.exists(key):
        raise KeyError(f"Key not found in backend: {key}")
    data = _load(backend)
    data[alias] = key
    _save(backend, data)
    return {"alias": alias, "key": key}


def get_alias(backend: BaseBackend, alias: str) -> str | None:
    """Return the key for alias, or None if unset."""
    return _load(backend).get(alias)


def delete_alias(backend: BaseBackend, alias: str) -> None:
    data = _load(backend)
    if alias not in data:
        raise KeyError(f"Alias not found: {alias}")
    del data[alias]
    _save(backend, data)


def list_aliases(backend: BaseBackend) -> dict:
    """Return all alias -> key mappings."""
    return _load(backend)


def resolve(backend: BaseBackend, alias_or_key: str) -> str:
    """Return the real key, resolving alias if needed."""
    mapping = _load(backend)
    return mapping.get(alias_or_key, alias_or_key)
