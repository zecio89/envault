"""Tests for envault.webhook."""

from __future__ import annotations

import json
from unittest.mock import patch, MagicMock

import pytest

from envault.backends.local import LocalBackend
from envault.webhook import (
    register_webhook,
    get_webhook,
    delete_webhook,
    list_webhooks,
    fire_event,
)


@pytest.fixture()
def backend(tmp_path):
    return LocalBackend(root=str(tmp_path))


def test_register_returns_record(backend):
    rec = register_webhook(backend, "slack", "https://hooks.example.com/abc", ["push"])
    assert rec["name"] == "slack"
    assert rec["url"] == "https://hooks.example.com/abc"
    assert rec["events"] == ["push"]


def test_register_deduplicates_events(backend):
    rec = register_webhook(backend, "ci", "https://ci.example.com", ["push", "push", "rotate"])
    assert rec["events"] == ["push", "rotate"]


def test_get_webhook_returns_record(backend):
    register_webhook(backend, "slack", "https://hooks.example.com/abc", ["push"])
    rec = get_webhook(backend, "slack")
    assert rec is not None
    assert rec["url"] == "https://hooks.example.com/abc"


def test_get_webhook_none_when_unregistered(backend):
    assert get_webhook(backend, "nonexistent") is None


def test_delete_webhook_returns_true(backend):
    register_webhook(backend, "slack", "https://hooks.example.com/abc", ["push"])
    assert delete_webhook(backend, "slack") is True
    assert get_webhook(backend, "slack") is None


def test_delete_webhook_returns_false_when_missing(backend):
    assert delete_webhook(backend, "ghost") is False


def test_list_webhooks_empty(backend):
    assert list_webhooks(backend) == []


def test_list_webhooks_returns_all(backend):
    register_webhook(backend, "slack", "https://a.example.com", ["push"])
    register_webhook(backend, "pagerduty", "https://b.example.com", ["rotate"])
    hooks = list_webhooks(backend)
    names = {h["name"] for h in hooks}
    assert names == {"slack", "pagerduty"}


def test_fire_event_calls_matching_webhooks(backend):
    register_webhook(backend, "slack", "https://hooks.example.com/abc", ["push", "rotate"])
    register_webhook(backend, "ci", "https://ci.example.com", ["pull"])

    mock_resp = MagicMock()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    mock_resp.status = 200

    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_open:
        results = fire_event(backend, "push", {"key": "production"})

    assert len(results) == 1
    assert results[0]["name"] == "slack"
    assert results[0]["ok"] is True
    mock_open.assert_called_once()


def test_fire_event_handles_http_error(backend):
    import urllib.error

    register_webhook(backend, "broken", "https://broken.example.com", ["push"])

    with patch("urllib.request.urlopen", side_effect=urllib.error.HTTPError(
        url=None, code=500, msg="Internal Server Error", hdrs=None, fp=None
    )):
        results = fire_event(backend, "push", {})

    assert results[0]["ok"] is False
    assert results[0]["status"] == 500


def test_fire_event_skips_unsubscribed(backend):
    register_webhook(backend, "slack", "https://hooks.example.com/abc", ["rotate"])
    with patch("urllib.request.urlopen") as mock_open:
        results = fire_event(backend, "push", {})
    assert results == []
    mock_open.assert_not_called()
