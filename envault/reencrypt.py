"""Re-encryption support for envault.

Allows bulk re-encryption of all environment blobs in a backend using a new
passphrase, without changing the stored key names or metadata structure.
Useful when rotating the master passphrase across an entire vault.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from envault.backends.base import BaseBackend
from envault.crypto import decrypt, encrypt


@dataclass
class ReencryptResult:
    """Summary of a bulk re-encryption operation."""

    total: int
    succeeded: List[str] = field(default_factory=list)
    failed: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)

    @property
    def all_ok(self) -> bool:
        """Return True if every key was re-encrypted successfully."""
        return len(self.failed) == 0

    @property
    def failure_count(self) -> int:
        return len(self.failed)


def reencrypt_all(
    backend: BaseBackend,
    old_passphrase: str,
    new_passphrase: str,
    *,
    prefix: Optional[str] = None,
    dry_run: bool = False,
) -> ReencryptResult:
    """Re-encrypt every env blob in *backend* from *old_passphrase* to *new_passphrase*.

    Parameters
    ----------
    backend:
        The storage backend whose keys should be re-encrypted.
    old_passphrase:
        The passphrase currently used to encrypt the stored blobs.
    new_passphrase:
        The passphrase that will be used after re-encryption.
    prefix:
        When provided, only keys whose names start with this string are
        processed.  Useful for targeting a single environment namespace.
    dry_run:
        When *True* the function performs all decryption checks but does **not**
        write any new ciphertext back to the backend.  The result still reports
        which keys *would* have been re-encrypted.

    Returns
    -------
    ReencryptResult
        A summary object listing succeeded, failed, and skipped keys.
    """
    all_keys = backend.list_keys()

    # Internal metadata keys (tags, ACLs, history …) are stored as JSON under
    # special prefixes.  We only want to touch plain env blobs, which do not
    # contain a "/" separator in their base name.  Keys that look like internal
    # records are skipped silently.
    _INTERNAL_SUFFIXES = (
        "/__tags__",
        "/__acl__",
        "/__history__",
        "/__lock__",
        "/__alias__",
        "/__annotation__",
        "/__checksum__",
        "/__expiry__",
        "/__pin__",
        "/__policy__",
        "/__quota__",
        "/__remind__",
        "/__snapshot__",
        "/__share__",
        "/__archive__",
        "/__webhook__",
        "/__namespace__",
    )

    env_keys = [
        k for k in all_keys
        if not any(k.endswith(suffix) for suffix in _INTERNAL_SUFFIXES)
    ]

    if prefix is not None:
        env_keys = [k for k in env_keys if k.startswith(prefix)]

    result = ReencryptResult(total=len(env_keys))

    for key in env_keys:
        try:
            ciphertext = backend.download(key)
            plaintext = decrypt(ciphertext, old_passphrase)
        except Exception:
            # Could not decrypt — wrong passphrase or corrupted blob.
            result.failed.append(key)
            continue

        if dry_run:
            result.succeeded.append(key)
            continue

        try:
            new_ciphertext = encrypt(plaintext, new_passphrase)
            backend.upload(key, new_ciphertext)
            result.succeeded.append(key)
        except Exception:
            result.failed.append(key)

    return result
