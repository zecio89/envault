"""Compare two stored env keys side-by-side."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from envault.crypto import decrypt
from envault.backends.base import BaseBackend


@dataclass
class CompareResult:
    only_in_a: List[str] = field(default_factory=list)
    only_in_b: List[str] = field(default_factory=list)
    same: List[str] = field(default_factory=list)
    different: List[str] = field(default_factory=list)


def _parse_env(blob: bytes) -> Dict[str, str]:
    result = {}
    for line in blob.decode().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, _, v = line.partition("=")
            result[k.strip()] = v.strip()
    return result


def compare_envs(
    backend: BaseBackend,
    key_a: str,
    key_b: str,
    passphrase_a: str,
    passphrase_b: Optional[str] = None,
) -> CompareResult:
    """Compare two encrypted env blobs stored in *backend*."""
    if passphrase_b is None:
        passphrase_b = passphrase_a

    if not backend.exists(key_a):
        raise KeyError(f"Key not found: {key_a}")
    if not backend.exists(key_b):
        raise KeyError(f"Key not found: {key_b}")

    blob_a = decrypt(backend.download(key_a), passphrase_a)
    blob_b = decrypt(backend.download(key_b), passphrase_b)

    env_a = _parse_env(blob_a)
    env_b = _parse_env(blob_b)

    keys_a = set(env_a)
    keys_b = set(env_b)

    result = CompareResult()
    result.only_in_a = sorted(keys_a - keys_b)
    result.only_in_b = sorted(keys_b - keys_a)
    for k in sorted(keys_a & keys_b):
        if env_a[k] == env_b[k]:
            result.same.append(k)
        else:
            result.different.append(k)
    return result
