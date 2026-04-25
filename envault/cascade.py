"""cascade.py — Merge multiple env keys in priority order (later sources override earlier)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from envault.crypto import decrypt, encrypt


@dataclass
class CascadeResult:
    merged: Dict[str, str] = field(default_factory=dict)
    sources: Dict[str, str] = field(default_factory=dict)  # key -> which env_key it came from
    overrides: List[Tuple[str, str, str]] = field(default_factory=list)  # (var, old_env, new_env)


def _parse_env(blob: str) -> Dict[str, str]:
    result: Dict[str, str] = {}
    for line in blob.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        k, _, v = line.partition("=")
        result[k.strip()] = v.strip()
    return result


def cascade_envs(
    backend,
    env_keys: List[str],
    passphrase: str,
    out_key: Optional[str] = None,
    out_passphrase: Optional[str] = None,
) -> CascadeResult:
    """Merge *env_keys* in order; later entries override earlier ones.

    If *out_key* is given the merged result is stored back to the backend
    encrypted with *out_passphrase* (falls back to *passphrase*).
    """
    result = CascadeResult()

    for env_key in env_keys:
        blob = decrypt(backend.download(env_key), passphrase)
        parsed = _parse_env(blob)
        for var, val in parsed.items():
            if var in result.merged:
                result.overrides.append((var, result.sources[var], env_key))
            result.merged[var] = val
            result.sources[var] = env_key

    if out_key is not None:
        lines = [f"{k}={v}" for k, v in sorted(result.merged.items())]
        merged_blob = "\n".join(lines)
        store_pass = out_passphrase or passphrase
        backend.upload(out_key, encrypt(merged_blob, store_pass))

    return result
