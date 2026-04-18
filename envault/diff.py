"""Diff two encrypted .env snapshots stored in a backend."""
from __future__ import annotations

from typing import Dict, List, Tuple

from envault.vault import Vault


def _parse_env(text: str) -> Dict[str, str]:
    """Parse KEY=VALUE lines into a dict, ignoring comments and blanks."""
    result: Dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, _, v = line.partition("=")
            result[k.strip()] = v.strip()
    return result


def diff_envs(
    vault: Vault,
    key_a: str,
    key_b: str,
    passphrase: str,
) -> List[Tuple[str, str | None, str | None]]:
    """Return a list of (variable, value_in_a, value_in_b) for changed keys.

    A value of None means the key is absent in that snapshot.
    Only keys that differ between the two snapshots are returned.
    """
    text_a = vault.pull(key_a, passphrase)
    text_b = vault.pull(key_b, passphrase)

    env_a = _parse_env(text_a)
    env_b = _parse_env(text_b)

    all_keys = set(env_a) | set(env_b)
    changes: List[Tuple[str, str | None, str | None]] = []

    for k in sorted(all_keys):
        v_a = env_a.get(k)
        v_b = env_b.get(k)
        if v_a != v_b:
            changes.append((k, v_a, v_b))

    return changes
