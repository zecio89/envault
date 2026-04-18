"""Simple access control list (ACL) for envault keys stored in the backend."""

import json
from typing import List, Optional
from envault.backends.base import BaseBackend

_ACL_PREFIX = "__acl__/"


def _acl_key(env_key: str) -> str:
    return f"{_ACL_PREFIX}{env_key}.json"


def set_acl(backend: BaseBackend, env_key: str, allowed_users: List[str]) -> dict:
    """Set the ACL for an env key. Raises KeyError if env_key doesn't exist."""
    if not backend.exists(env_key):
        raise KeyError(f"Key '{env_key}' does not exist in backend.")
    acl = {"key": env_key, "allowed_users": sorted(set(allowed_users))}
    backend.upload(_acl_key(env_key), json.dumps(acl).encode())
    return acl


def get_acl(backend: BaseBackend, env_key: str) -> dict:
    """Return the ACL for an env key, or empty allowed_users if none set."""
    k = _acl_key(env_key)
    if not backend.exists(k):
        return {"key": env_key, "allowed_users": []}
    data = backend.download(k)
    return json.loads(data.decode())


def delete_acl(backend: BaseBackend, env_key: str) -> None:
    """Remove the ACL entry for an env key."""
    k = _acl_key(env_key)
    if backend.exists(k):
        backend.delete(k)


def is_allowed(backend: BaseBackend, env_key: str, user: str) -> bool:
    """Return True if user is in the ACL for env_key, or if no ACL is set."""
    acl = get_acl(backend, env_key)
    if not acl["allowed_users"]:
        return True
    return user in acl["allowed_users"]


def list_acls(backend: BaseBackend) -> List[dict]:
    """Return all ACL entries stored in the backend."""
    all_keys = backend.list_keys()
    result = []
    for k in all_keys:
        if k.startswith(_ACL_PREFIX) and k.endswith(".json"):
            data = backend.download(k)
            result.append(json.loads(data.decode()))
    return result
