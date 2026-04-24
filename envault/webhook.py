"""Webhook notification support for envault events."""

from __future__ import annotations

import json
import urllib.request
import urllib.error
from typing import Any

from envault.backends.base import BaseBackend

_WEBHOOK_KEY = "__webhooks__"


def _load(backend: BaseBackend) -> dict[str, Any]:
    if not backend.exists(_WEBHOOK_KEY):
        return {}
    raw = backend.download(_WEBHOOK_KEY)
    return json.loads(raw.decode())


def _save(backend: BaseBackend, data: dict[str, Any]) -> None:
    backend.upload(_WEBHOOK_KEY, json.dumps(data).encode())


def register_webhook(backend: BaseBackend, name: str, url: str, events: list[str]) -> dict[str, Any]:
    """Register a named webhook URL for a list of event types."""
    data = _load(backend)
    record = {"url": url, "events": sorted(set(events))}
    data[name] = record
    _save(backend, data)
    return {"name": name, **record}


def get_webhook(backend: BaseBackend, name: str) -> dict[str, Any] | None:
    """Return the webhook record for *name*, or None if not registered."""
    return _load(backend).get(name)


def delete_webhook(backend: BaseBackend, name: str) -> bool:
    """Remove a webhook by name. Returns True if it existed."""
    data = _load(backend)
    if name not in data:
        return False
    del data[name]
    _save(backend, data)
    return True


def list_webhooks(backend: BaseBackend) -> list[dict[str, Any]]:
    """Return all registered webhooks."""
    data = _load(backend)
    return [{"name": k, **v} for k, v in data.items()]


def fire_event(backend: BaseBackend, event: str, payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Send *payload* to every webhook subscribed to *event*.

    Returns a list of result dicts with keys ``name``, ``url``, ``ok``, ``status``.
    """
    results: list[dict[str, Any]] = []
    body = json.dumps({"event": event, **payload}).encode()
    for hook in list_webhooks(backend):
        if event not in hook["events"]:
            continue
        try:
            req = urllib.request.Request(
                hook["url"],
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                status = resp.status
                ok = 200 <= status < 300
        except urllib.error.HTTPError as exc:
            status = exc.code
            ok = False
        except Exception:
            status = 0
            ok = False
        results.append({"name": hook["name"], "url": hook["url"], "ok": ok, "status": status})
    return results
