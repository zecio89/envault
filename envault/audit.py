"""Audit log for vault operations."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

DEFAULT_LOG_PATH = Path.home() / ".envault" / "audit.log"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def log_event(
    action: str,
    key: str,
    user: Optional[str] = None,
    backend: Optional[str] = None,
    log_path: Path = DEFAULT_LOG_PATH,
) -> dict:
    """Append a structured audit event to the log file."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "timestamp": _now_iso(),
        "action": action,
        "key": key,
        "user": user or os.environ.get("USER", "unknown"),
        "backend": backend or "unknown",
    }
    with log_path.open("a") as f:
        f.write(json.dumps(event) + "\n")
    return event


def read_events(log_path: Path = DEFAULT_LOG_PATH) -> List[dict]:
    """Return all audit events from the log file."""
    if not log_path.exists():
        return []
    events = []
    with log_path.open("r") as f:
        for line in f:
            line = line.strip()
            if line:
                events.append(json.loads(line))
    return events


def clear_log(log_path: Path = DEFAULT_LOG_PATH) -> None:
    """Delete the audit log file."""
    if log_path.exists():
        log_path.unlink()
