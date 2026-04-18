"""Lock/unlock support: temporarily disable access to an env by storing a lock marker."""

from __future__ import annotations

LOCK_SUFFIX = ".lock"


def _lock_key(env_key: str) -> str:
    return env_key + LOCK_SUFFIX


def lock_env(backend, env_key: str) -> str:
    """Lock an env entry. Raises KeyError if env_key does not exist."""
    if not backend.exists(env_key):
        raise KeyError(f"No such env: {env_key!r}")
    lock_key = _lock_key(env_key)
    backend.upload(lock_key, b"locked")
    return lock_key


def unlock_env(backend, env_key: str) -> None:
    """Unlock an env entry. Raises KeyError if not currently locked."""
    lock_key = _lock_key(env_key)
    if not backend.exists(lock_key):
        raise KeyError(f"Env {env_key!r} is not locked")
    backend.delete(lock_key)


def is_locked(backend, env_key: str) -> bool:
    """Return True if the env entry is currently locked."""
    return backend.exists(_lock_key(env_key))


def list_locked(backend) -> list[str]:
    """Return env keys (without suffix) that are currently locked."""
    all_keys = backend.list_keys()
    return [
        k[: -len(LOCK_SUFFIX)]
        for k in all_keys
        if k.endswith(LOCK_SUFFIX)
    ]
