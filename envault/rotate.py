"""Key rotation: re-encrypt stored envs with a new passphrase."""
from __future__ import annotations

from typing import TYPE_CHECKING

from envault.crypto import decrypt, encrypt
from envault.audit import log_event

if TYPE_CHECKING:
    from envault.backends.base import BaseBackend


def rotate_key(
    backend: "BaseBackend",
    old_passphrase: str,
    new_passphrase: str,
    prefix: str = "",
) -> list[str]:
    """Re-encrypt every env stored in *backend* under a new passphrase.

    Returns the list of keys that were rotated.
    Raises on the first decryption failure so the caller can abort.
    """
    keys = backend.list_keys()
    if prefix:
        keys = [k for k in keys if k.startswith(prefix)]

    rotated: list[str] = []
    for key in keys:
        ciphertext = backend.download(key)
        plaintext = decrypt(ciphertext, old_passphrase)          # raises on bad passphrase
        new_ciphertext = encrypt(plaintext, new_passphrase)
        backend.upload(key, new_ciphertext)
        log_event("rotate", {"key": key})
        rotated.append(key)

    return rotated
