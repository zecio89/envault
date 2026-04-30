"""envault.sign — HMAC-based signing and verification of stored env blobs."""
from __future__ import annotations

import hashlib
import hmac
import json
from typing import Optional

from envault.backends.base import BaseBackend

_SIG_PREFIX = "__sig__/"


def _sig_key(env_key: str) -> str:
    return f"{_SIG_PREFIX}{env_key}"


def _compute_hmac(blob: bytes, secret: str) -> str:
    """Return a hex-encoded HMAC-SHA256 digest."""
    return hmac.new(secret.encode(), blob, hashlib.sha256).hexdigest()


def sign_env(backend: BaseBackend, env_key: str, secret: str) -> dict:
    """Compute and store an HMAC signature for *env_key*.

    Raises KeyError if *env_key* does not exist in the backend.
    """
    if not backend.exists(env_key):
        raise KeyError(f"Key not found: {env_key}")

    blob = backend.download(env_key)
    digest = _compute_hmac(blob, secret)
    record = {"env_key": env_key, "algorithm": "hmac-sha256", "digest": digest}
    backend.upload(_sig_key(env_key), json.dumps(record).encode())
    return record


def get_signature(backend: BaseBackend, env_key: str) -> Optional[dict]:
    """Return the stored signature record for *env_key*, or None."""
    sig_key = _sig_key(env_key)
    if not backend.exists(sig_key):
        return None
    return json.loads(backend.download(sig_key).decode())


def verify_signature(backend: BaseBackend, env_key: str, secret: str) -> bool:
    """Return True if the stored signature matches the current blob.

    Returns False if no signature is stored or the digest does not match.
    Raises KeyError if *env_key* does not exist.
    """
    if not backend.exists(env_key):
        raise KeyError(f"Key not found: {env_key}")

    record = get_signature(backend, env_key)
    if record is None:
        return False

    blob = backend.download(env_key)
    expected = _compute_hmac(blob, secret)
    return hmac.compare_digest(expected, record["digest"])


def delete_signature(backend: BaseBackend, env_key: str) -> bool:
    """Remove the signature for *env_key*. Returns True if one existed."""
    sig_key = _sig_key(env_key)
    if backend.exists(sig_key):
        backend.delete(sig_key)
        return True
    return False


def list_signed(backend: BaseBackend) -> list[str]:
    """Return env keys that have a stored signature."""
    return [
        k[len(_SIG_PREFIX):]
        for k in backend.list_keys()
        if k.startswith(_SIG_PREFIX)
    ]
