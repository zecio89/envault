"""Watch a local .env file and auto-push on change."""
from __future__ import annotations

import hashlib
import time
from pathlib import Path
from typing import Callable, Optional


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def watch_file(
    path: Path,
    on_change: Callable[[Path], None],
    *,
    interval: float = 1.0,
    max_iterations: Optional[int] = None,
) -> None:
    """Poll *path* every *interval* seconds; call *on_change* when it changes.

    Args:
        path: The file to watch.
        on_change: Callback invoked with the file path when a change is detected.
        interval: Polling interval in seconds.
        max_iterations: Stop after this many iterations (useful for testing).
    """
    if not path.exists():
        raise FileNotFoundError(f"Watch target not found: {path}")

    last_hash = _file_hash(path)
    iterations = 0

    while True:
        time.sleep(interval)
        iterations += 1

        if path.exists():
            current_hash = _file_hash(path)
            if current_hash != last_hash:
                last_hash = current_hash
                on_change(path)

        if max_iterations is not None and iterations >= max_iterations:
            break
