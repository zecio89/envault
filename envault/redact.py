"""Redact sensitive values from env blobs before display or logging."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

# Keys whose values should always be fully redacted
_SENSITIVE_PATTERNS: List[re.Pattern] = [
    re.compile(r"(secret|password|passwd|token|api[_]?key|private[_]?key|auth|credential)", re.IGNORECASE),
]

_REDACT_PLACEHOLDER = "***REDACTED***"
_PARTIAL_SHOW = 4  # characters to reveal at start/end for partial mode


@dataclass
class RedactResult:
    original_count: int
    redacted_count: int
    lines: List[str] = field(default_factory=list)

    @property
    def all_clear(self) -> bool:
        return self.redacted_count == 0


def _is_sensitive(key: str) -> bool:
    """Return True if the key name matches any sensitive pattern."""
    return any(p.search(key) for p in _SENSITIVE_PATTERNS)


def _partial_redact(value: str) -> str:
    """Show first and last N chars, mask the middle."""
    if len(value) <= _PARTIAL_SHOW * 2:
        return _REDACT_PLACEHOLDER
    return value[:_PARTIAL_SHOW] + "***" + value[-_PARTIAL_SHOW:]


def redact_env(
    content: str,
    partial: bool = False,
    extra_keys: Optional[List[str]] = None,
) -> RedactResult:
    """Redact sensitive values in a dotenv-formatted string.

    Args:
        content:    Raw dotenv text.
        partial:    If True, show partial values instead of full redaction.
        extra_keys: Additional key names to treat as sensitive.

    Returns:
        RedactResult with processed lines and counts.
    """
    extra_set = {k.upper() for k in (extra_keys or [])}
    lines_out: List[str] = []
    original_count = 0
    redacted_count = 0

    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            lines_out.append(line)
            continue

        if "=" not in stripped:
            lines_out.append(line)
            continue

        original_count += 1
        key, _, value = stripped.partition("=")
        key = key.strip()
        value = value.strip()

        if _is_sensitive(key) or key.upper() in extra_set:
            redacted_count += 1
            replacement = _partial_redact(value) if partial else _REDACT_PLACEHOLDER
            lines_out.append(f"{key}={replacement}")
        else:
            lines_out.append(line)

    return RedactResult(
        original_count=original_count,
        redacted_count=redacted_count,
        lines=lines_out,
    )
