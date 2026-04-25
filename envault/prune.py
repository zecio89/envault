"""Prune stale or expired environment keys from the backend."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from envault.backends.base import BaseBackend
from envault.expiry import get_expiry

try:
    from datetime import datetime, timezone
except ImportError:
    from datetime import datetime


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class PruneResult:
    pruned: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def total_pruned(self) -> int:
        return len(self.pruned)

    @property
    def all_ok(self) -> bool:
        return len(self.errors) == 0


def prune_expired(
    backend: BaseBackend,
    keys: Optional[List[str]] = None,
    dry_run: bool = False,
) -> PruneResult:
    """Delete all keys whose expiry date has passed.

    Args:
        backend: Storage backend to operate on.
        keys: Explicit list of keys to inspect. Defaults to all keys.
        dry_run: If True, report what would be pruned without deleting.

    Returns:
        PruneResult summarising pruned, skipped, and errored keys.
    """
    result = PruneResult()
    now = _now_iso()

    candidates = keys if keys is not None else backend.list_keys()

    for key in candidates:
        # Skip internal metadata keys
        if key.startswith("__"):
            result.skipped.append(key)
            continue

        try:
            info = get_expiry(backend, key)
        except Exception as exc:  # noqa: BLE001
            result.errors.append(f"{key}: {exc}")
            continue

        if info is None:
            result.skipped.append(key)
            continue

        expires_at: str = info.get("expires_at", "")
        if expires_at and expires_at <= now:
            if not dry_run:
                try:
                    backend.delete(key)
                except Exception as exc:  # noqa: BLE001
                    result.errors.append(f"{key}: {exc}")
                    continue
            result.pruned.append(key)
        else:
            result.skipped.append(key)

    return result
