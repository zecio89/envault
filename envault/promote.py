"""Promote an env key from one environment to another (e.g. staging -> production)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from envault.backends.base import BaseBackend
from envault.crypto import decrypt, encrypt


@dataclass
class PromoteResult:
    source_key: str
    dest_key: str
    re_encrypted: bool


def promote_env(
    backend: BaseBackend,
    source_key: str,
    dest_key: str,
    source_passphrase: str,
    dest_passphrase: Optional[str] = None,
    overwrite: bool = False,
) -> PromoteResult:
    """Copy an encrypted env from *source_key* to *dest_key*.

    If *dest_passphrase* is provided the blob is re-encrypted with the new
    passphrase; otherwise the original ciphertext is stored as-is (both
    environments share the same passphrase).

    Raises
    ------
    KeyError
        If *source_key* does not exist in the backend.
    FileExistsError
        If *dest_key* already exists and *overwrite* is False.
    """
    if not backend.exists(source_key):
        raise KeyError(f"Source key not found in backend: {source_key!r}")

    if backend.exists(dest_key) and not overwrite:
        raise FileExistsError(
            f"Destination key already exists: {dest_key!r}. "
            "Pass overwrite=True to replace it."
        )

    blob = backend.download(source_key)

    re_encrypted = False
    if dest_passphrase is not None and dest_passphrase != source_passphrase:
        plaintext = decrypt(blob.decode(), source_passphrase)
        blob = encrypt(plaintext, dest_passphrase).encode()
        re_encrypted = True

    backend.upload(dest_key, blob)

    return PromoteResult(
        source_key=source_key,
        dest_key=dest_key,
        re_encrypted=re_encrypted,
    )
