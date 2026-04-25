"""Namespace support: group env keys under logical namespaces (e.g. 'prod/db', 'staging/app')."""

from __future__ import annotations

import json
from typing import Optional

from envault.backends.base import BaseBackend

_NS_INDEX_KEY = "__namespaces__/index.json"


def _load_index(backend: BaseBackend) -> dict[str, list[str]]:
    """Return the namespace -> [env_keys] mapping."""
    if not backend.exists(_NS_INDEX_KEY):
        return {}
    raw = backend.download(_NS_INDEX_KEY)
    return json.loads(raw.decode())


def _save_index(backend: BaseBackend, index: dict[str, list[str]]) -> None:
    backend.upload(_NS_INDEX_KEY, json.dumps(index, indent=2).encode())


def assign_namespace(backend: BaseBackend, env_key: str, namespace: str) -> dict:
    """Assign *env_key* to *namespace*. Creates namespace if it doesn't exist."""
    if not backend.exists(env_key):
        raise KeyError(f"env key not found in backend: {env_key!r}")
    index = _load_index(backend)
    # Remove from any existing namespace first
    for ns, keys in index.items():
        if env_key in keys and ns != namespace:
            keys.remove(env_key)
    ns_keys = index.setdefault(namespace, [])
    if env_key not in ns_keys:
        ns_keys.append(env_key)
    _save_index(backend, index)
    return {"namespace": namespace, "env_key": env_key}


def remove_from_namespace(backend: BaseBackend, env_key: str, namespace: str) -> bool:
    """Remove *env_key* from *namespace*. Returns True if it was present."""
    index = _load_index(backend)
    ns_keys = index.get(namespace, [])
    if env_key not in ns_keys:
        return False
    ns_keys.remove(env_key)
    if not ns_keys:
        del index[namespace]
    _save_index(backend, index)
    return True


def list_namespaces(backend: BaseBackend) -> list[str]:
    """Return all defined namespace names."""
    return sorted(_load_index(backend).keys())


def get_namespace_keys(backend: BaseBackend, namespace: str) -> list[str]:
    """Return env keys assigned to *namespace*."""
    return list(_load_index(backend).get(namespace, []))


def delete_namespace(backend: BaseBackend, namespace: str) -> bool:
    """Delete a namespace (does not delete the env keys themselves)."""
    index = _load_index(backend)
    if namespace not in index:
        return False
    del index[namespace]
    _save_index(backend, index)
    return True
