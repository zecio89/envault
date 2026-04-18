"""Tests for envault.audit module."""

import pytest
from pathlib import Path
from envault.audit import log_event, read_events, clear_log


@pytest.fixture
def log_path(tmp_path):
    return tmp_path / "test_audit.log"


def test_log_event_creates_file(log_path):
    log_event("push", "prod/app", log_path=log_path)
    assert log_path.exists()


def test_log_event_returns_dict(log_path):
    event = log_event("push", "prod/app", user="alice", backend="local", log_path=log_path)
    assert event["action"] == "push"
    assert event["key"] == "prod/app"
    assert event["user"] == "alice"
    assert event["backend"] == "local"
    assert "timestamp" in event


def test_read_events_empty_when_no_log(log_path):
    events = read_events(log_path=log_path)
    assert events == []


def test_read_events_returns_all(log_path):
    log_event("push", "dev/app", log_path=log_path)
    log_event("pull", "dev/app", log_path=log_path)
    events = read_events(log_path=log_path)
    assert len(events) == 2
    assert events[0]["action"] == "push"
    assert events[1]["action"] == "pull"


def test_multiple_keys_logged(log_path):
    log_event("push", "prod/app", log_path=log_path)
    log_event("push", "staging/app", log_path=log_path)
    events = read_events(log_path=log_path)
    keys = [e["key"] for e in events]
    assert "prod/app" in keys
    assert "staging/app" in keys


def test_clear_log(log_path):
    log_event("push", "prod/app", log_path=log_path)
    clear_log(log_path=log_path)
    assert not log_path.exists()
    assert read_events(log_path=log_path) == []


def test_clear_log_no_file_is_noop(log_path):
    clear_log(log_path=log_path)  # should not raise
