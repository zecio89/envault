"""Checksum tracking for vault entries.

Records and verifies SHA-256 checksums of encrypted blobs so that
tampering or accidental corruption can be detected.
"""

from __future__ import annotations

import hashlib
import json
from typing import Optional

from envault.backends.base import BaseBackend

_CHECKSUM_PREFIX = "__checksums__/"


def _checksum_key(env_key: str) -> str:
    return f"{_CHECKSUM_PREFIX}{env_key}.json"


def _compute(blob: bytes) -> str:
    """Return the hex SHA-256 digest of *blob*."""
    return hashlib.sha256(blob).hexdigest()


def record_checksum(backend: BaseBackend, env_key: str) -> dict:
    """Compute and store the checksum for an existing vault entry.

    Parameters
    ----------
    backend:
        The storage backend that holds *env_key*.
    env_key:
        The vault key whose blob should be checksummed.

    Returns
    -------
    dict with keys ``env_key``, ``algorithm``, and ``checksum``.

    Raises
    ------
    KeyError
        If *env_key* does not exist in the backend.
    """
    if not backend.exists(env_key):
        raise KeyError(f"Key not found in backend: {env_key!r}")

    blob = backend.download(env_key)
    digest = _compute(blob)
    record = {"env_key": env_key, "algorithm": "sha256", "checksum": digest}
    backend.upload(_checksum_key(env_key), json.dumps(record).encode())
    return record


def get_checksum(backend: BaseBackend, env_key: str) -> Optional[dict]:
    """Retrieve the stored checksum record for *env_key*, or ``None``."""
    ck = _checksum_key(env_key)
    if not backend.exists(ck):
        return None
    return json.loads(backend.download(ck).decode())


def verify_checksum(backend: BaseBackend, env_key: str) -> bool:
    """Return ``True`` if the stored checksum matches the current blob.

    Returns ``False`` if the checksum record is missing or the digest
    does not match.
    """
    record = get_checksum(backend, env_key)
    if record is None:
        return False
    if not backend.exists(env_key):
        return False
    blob = backend.download(env_key)
    return _compute(blob) == record["checksum"]


def delete_checksum(backend: BaseBackend, env_key: str) -> None:
    """Remove the checksum record for *env_key* if it exists."""
    ck = _checksum_key(env_key)
    if backend.exists(ck):
        backend.delete(ck)
