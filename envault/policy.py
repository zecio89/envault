"""Policy enforcement: define and check access policies for env keys."""

from __future__ import annotations

import json
from typing import Any

from envault.backends.base import BaseBackend

_POLICY_PREFIX = "__policy__/"


def _policy_key(env_key: str) -> str:
    return f"{_POLICY_PREFIX}{env_key}"


def set_policy(
    backend: BaseBackend,
    env_key: str,
    *,
    allowed_users: list[str] | None = None,
    read_only: bool = False,
    max_age_days: int | None = None,
) -> dict[str, Any]:
    """Attach a policy record to an env key."""
    if not backend.exists(env_key):
        raise KeyError(f"Key not found in backend: {env_key}")

    policy: dict[str, Any] = {
        "env_key": env_key,
        "allowed_users": sorted(set(allowed_users)) if allowed_users else [],
        "read_only": read_only,
        "max_age_days": max_age_days,
    }
    backend.upload(_policy_key(env_key), json.dumps(policy).encode())
    return policy


def get_policy(backend: BaseBackend, env_key: str) -> dict[str, Any] | None:
    """Return the policy for an env key, or None if not set."""
    pk = _policy_key(env_key)
    if not backend.exists(pk):
        return None
    return json.loads(backend.download(pk).decode())


def delete_policy(backend: BaseBackend, env_key: str) -> None:
    """Remove the policy attached to an env key."""
    pk = _policy_key(env_key)
    if backend.exists(pk):
        backend.delete(pk)


def is_allowed(backend: BaseBackend, env_key: str, user: str) -> bool:
    """Return True if the user is permitted by the policy (or no policy exists)."""
    policy = get_policy(backend, env_key)
    if policy is None:
        return True
    allowed = policy.get("allowed_users", [])
    return len(allowed) == 0 or user in allowed


def list_policies(backend: BaseBackend) -> list[str]:
    """Return env keys that have an associated policy."""
    prefix_len = len(_POLICY_PREFIX)
    return [
        k[prefix_len:]
        for k in backend.list_keys()
        if k.startswith(_POLICY_PREFIX)
    ]
