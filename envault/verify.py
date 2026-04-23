"""Verify integrity of stored encrypted env blobs."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from envault.backends.base import BaseBackend
from envault.crypto import decrypt


@dataclass
class VerifyResult:
    key: str
    ok: bool
    error: Optional[str] = None


@dataclass
class VerifySummary:
    results: List[VerifyResult] = field(default_factory=list)

    @property
    def passed(self) -> List[VerifyResult]:
        return [r for r in self.results if r.ok]

    @property
    def failed(self) -> List[VerifyResult]:
        return [r for r in self.results if not r.ok]

    @property
    def all_ok(self) -> bool:
        return all(r.ok for r in self.results)


def verify_env(
    backend: BaseBackend,
    passphrase: str,
    key: Optional[str] = None,
) -> VerifySummary:
    """Attempt to decrypt one or all env blobs to verify integrity.

    Args:
        backend: Storage backend to read from.
        passphrase: Passphrase used to decrypt the blobs.
        key: If provided, verify only this key; otherwise verify all keys.

    Returns:
        VerifySummary with per-key results.
    """
    keys_to_check = [key] if key else backend.list_keys()
    summary = VerifySummary()

    for k in keys_to_check:
        # Skip internal metadata keys (prefixed with __)
        if k.startswith("__"):
            continue
        try:
            blob = backend.download(k)
            decrypt(blob, passphrase)
            summary.results.append(VerifyResult(key=k, ok=True))
        except Exception as exc:  # noqa: BLE001
            summary.results.append(VerifyResult(key=k, ok=False, error=str(exc)))

    return summary
