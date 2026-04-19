"""Tests for envault.watch."""
from __future__ import annotations

import time
from pathlib import Path

import pytest

from envault.watch import watch_file


def test_watch_detects_change(tmp_path: Path) -> None:
    f = tmp_path / "test.env"
    f.write_text("A=1\n")

    calls: list[Path] = []

    def on_change(p: Path) -> None:
        calls.append(p)

    # We'll mutate the file mid-watch using a side-effect in on_change.
    # Use max_iterations=3 with interval=0 to keep test fast.
    iteration = 0
    original_sleep = time.sleep

    def fake_sleep(secs: float) -> None:  # noqa: ARG001
        nonlocal iteration
        iteration += 1
        if iteration == 1:
            f.write_text("A=2\n")  # trigger change on first poll

    import unittest.mock as mock

    with mock.patch("envault.watch.time.sleep", side_effect=fake_sleep):
        watch_file(f, on_change, interval=0.0, max_iterations=3)

    assert len(calls) == 1
    assert calls[0] == f


def test_watch_no_change(tmp_path: Path) -> None:
    f = tmp_path / "stable.env"
    f.write_text("X=1\n")
    calls: list[Path] = []

    import unittest.mock as mock

    with mock.patch("envault.watch.time.sleep"):
        watch_file(f, lambda p: calls.append(p), interval=0.0, max_iterations=3)

    assert calls == []


def test_watch_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        watch_file(tmp_path / "nope.env", lambda p: None, max_iterations=1)


def test_watch_calls_on_change_multiple_times(tmp_path: Path) -> None:
    f = tmp_path / "multi.env"
    f.write_text("A=1\n")
    calls: list[int] = []
    iteration = 0

    def fake_sleep(_: float) -> None:
        nonlocal iteration
        iteration += 1
        f.write_text(f"A={iteration}\n")

    import unittest.mock as mock

    with mock.patch("envault.watch.time.sleep", side_effect=fake_sleep):
        watch_file(f, lambda p: calls.append(1), interval=0.0, max_iterations=3)

    assert len(calls) == 3
