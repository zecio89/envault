"""Import encrypted envs from another backend or local archive."""
from __future__ import annotations

from typing import List

from envault.backends.base import BaseBackend
from envault.crypto import decrypt, encrypt


def import_env(
    source_backend: BaseBackend,
    dest_backend: BaseBackend,
    old_passphrase: str,
    new_passphrase: str,
    keys: List[str] | None = None,
    overwrite: bool = False,
) -> List[str]:
    """Copy encrypted envs from *source_backend* into *dest_backend*.

    Each secret is re-encrypted under *new_passphrase* so the destination
    never receives the source passphrase.

    Args:
        source_backend: Backend to read from.
        dest_backend:   Backend to write to.
        old_passphrase: Passphrase used in the source backend.
        new_passphrase: Passphrase to use in the destination backend.
        keys:           Explicit list of keys to import; defaults to all.
        overwrite:      If False, skip keys that already exist in dest.

    Returns:
        List of keys that were successfully imported.
    """
    if keys is None:
        keys = source_backend.list_keys()

    imported: List[str] = []

    for key in keys:
        if not overwrite and dest_backend.exists(key):
            continue

        ciphertext = source_backend.download(key)
        plaintext = decrypt(ciphertext, old_passphrase)
        new_ciphertext = encrypt(plaintext, new_passphrase)
        dest_backend.upload(key, new_ciphertext)
        imported.append(key)

    return imported
