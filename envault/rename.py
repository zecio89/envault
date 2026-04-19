"""Rename an env key in the backend, preserving content and metadata."""
from __future__ import annotations

from envault.backends.base import BaseBackend


def rename_env(backend: BaseBackend, old_key: str, new_key: str, passphrase: str) -> dict:
    """Rename *old_key* to *new_key* in *backend*.

    Copies the encrypted blob to the new key, then deletes the old one.
    Returns a dict with ``old_key`` and ``new_key``.

    Raises:
        KeyError: if *old_key* does not exist.
        ValueError: if *new_key* already exists.
    """
    if not backend.exists(old_key):
        raise KeyError(f"Key not found: {old_key!r}")
    if backend.exists(new_key):
        raise ValueError(f"Destination key already exists: {new_key!r}")

    blob = backend.download(old_key)
    backend.upload(new_key, blob)
    backend.delete(old_key)

    return {"old_key": old_key, "new_key": new_key}
