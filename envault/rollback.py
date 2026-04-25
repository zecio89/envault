"""rollback.py — Roll back an env key to a previous version from history."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from envault.backends.base import BaseBackend
from envault.history import get_history, record_version, restore_version
from envault.crypto import decrypt, encrypt


@dataclass
class RollbackResult:
    key: str
    rolled_back_to: str   # version id
    previous_version: Optional[str]  # version id that was active before
    blob: str


def rollback_env(
    backend: BaseBackend,
    key: str,
    version_id: str,
    passphrase: str,
    new_passphrase: Optional[str] = None,
) -> RollbackResult:
    """Roll back *key* to the blob stored under *version_id*.

    If *new_passphrase* is provided the blob is re-encrypted with it;
    otherwise the original *passphrase* is reused.

    The restored blob is written back to the backend and a new history
    entry is recorded so the rollback itself is auditable.

    Raises
    ------
    KeyError
        If *key* does not exist in the backend or *version_id* is not
        found in the history log for that key.
    ValueError
        If the stored blob cannot be decrypted with *passphrase*.
    """
    if not backend.exists(key):
        raise KeyError(f"Key not found in backend: {key!r}")

    history = get_history(backend, key)
    if not history:
        raise KeyError(f"No history recorded for key: {key!r}")

    # Locate the requested version
    entry = next((e for e in history if e["version_id"] == version_id), None)
    if entry is None:
        raise KeyError(
            f"Version {version_id!r} not found in history for key {key!r}"
        )

    # Fetch and verify the blob is decryptable
    blob = restore_version(backend, key, version_id)
    plaintext = decrypt(blob, passphrase)  # raises ValueError on bad passphrase

    # Re-encrypt if a new passphrase was supplied
    target_passphrase = new_passphrase or passphrase
    if new_passphrase:
        blob = encrypt(plaintext, new_passphrase)

    # Determine what the current version is before we overwrite
    current_history = get_history(backend, key)
    previous_version_id: Optional[str] = (
        current_history[-1]["version_id"] if current_history else None
    )

    # Write back
    backend.upload(key, blob)

    # Record the rollback as a new history entry
    record_version(backend, key, blob, target_passphrase)

    return RollbackResult(
        key=key,
        rolled_back_to=version_id,
        previous_version=previous_version_id,
        blob=blob,
    )
