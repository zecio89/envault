"""Merge two encrypted env blobs, with conflict resolution."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envault.crypto import decrypt, encrypt


@dataclass
class MergeResult:
    merged: Dict[str, str] = field(default_factory=dict)
    conflicts: Dict[str, tuple] = field(default_factory=dict)  # key -> (base, other)
    added: List[str] = field(default_factory=list)
    removed: List[str] = field(default_factory=list)


def _parse_env(text: str) -> Dict[str, str]:
    result = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        k, _, v = line.partition("=")
        result[k.strip()] = v.strip()
    return result


def _serialize_env(env: Dict[str, str]) -> str:
    return "\n".join(f"{k}={v}" for k, v in sorted(env.items())) + "\n"


def merge_envs(
    base_blob: str,
    other_blob: str,
    base_passphrase: str,
    other_passphrase: str,
    out_passphrase: str,
    strategy: str = "ours",
) -> MergeResult:
    """Merge two encrypted env blobs.

    strategy: 'ours' keeps base value on conflict, 'theirs' keeps other value.
    """
    if strategy not in ("ours", "theirs"):
        raise ValueError(f"Unknown strategy: {strategy!r}. Use 'ours' or 'theirs'.")

    base_text = decrypt(base_blob, base_passphrase)
    other_text = decrypt(other_blob, other_passphrase)

    base_env = _parse_env(base_text)
    other_env = _parse_env(other_text)

    result = MergeResult()
    merged: Dict[str, str] = {}

    all_keys = set(base_env) | set(other_env)
    for key in all_keys:
        in_base = key in base_env
        in_other = key in other_env
        if in_base and not in_other:
            merged[key] = base_env[key]
            result.removed.append(key)
        elif in_other and not in_base:
            merged[key] = other_env[key]
            result.added.append(key)
        elif base_env[key] == other_env[key]:
            merged[key] = base_env[key]
        else:
            result.conflicts[key] = (base_env[key], other_env[key])
            merged[key] = base_env[key] if strategy == "ours" else other_env[key]

    result.merged = merged
    serialized = _serialize_env(merged)
    result.merged["__blob__"] = encrypt(serialized, out_passphrase)
    return result
