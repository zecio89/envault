"""Clone an env entry from one key to another, optionally across backends."""

from __future__ import annotations

from typing import Optional

from envault.backends.base import BaseBackend
from envault.crypto import decrypt, encrypt


def clone_env(
    source_backend: BaseBackend,
    source_key: str,
    dest_backend: BaseBackend,
    dest_key: str,
    passphrase: str,
    new_passphrase: Optional[str] = None,
    overwrite: bool = False,
) -> dict:
    """Clone *source_key* into *dest_key*.

    If *new_passphrase* is provided the cloned blob is re-encrypted with it;
    otherwise the original passphrase is reused.

    Returns a dict with ``source_key``, ``dest_key``, and ``reencrypted``.

    Raises ``KeyError`` if *source_key* does not exist.
    Raises ``FileExistsError`` if *dest_key* already exists and *overwrite* is False.
    """
    if not source_backend.exists(source_key):
        raise KeyError(f"Source key not found: {source_key!r}")

    if not overwrite and dest_backend.exists(dest_key):
        raise FileExistsError(
            f"Destination key already exists: {dest_key!r}. "
            "Pass overwrite=True to replace it."
        )

    blob = source_backend.download(source_key)
    plaintext = decrypt(blob, passphrase)

    target_passphrase = new_passphrase if new_passphrase is not None else passphrase
    new_blob = encrypt(plaintext, target_passphrase)

    dest_backend.upload(dest_key, new_blob)

    return {
        "source_key": source_key,
        "dest_key": dest_key,
        "reencrypted": new_passphrase is not None,
    }
