"""Tag management for envault: attach metadata tags to stored env keys."""
from __future__ import annotations
import json
from typing import Dict, List, Optional
from envault.backends.base import BaseBackend

TAGS_SUFFIX = ".__tags__.json"


def _tags_key(env_key: str) -> str:
    return env_key + TAGS_SUFFIX


def set_tags(backend: BaseBackend, env_key: str, tags: Dict[str, str]) -> None:
    """Persist tags dict for the given env key."""
    if not backend.exists(env_key):
        raise KeyError(f"env key not found: {env_key}")
    payload = json.dumps(tags).encode()
    backend.upload(_tags_key(env_key), payload)


def get_tags(backend: BaseBackend, env_key: str) -> Dict[str, str]:
    """Return tags for the given env key, or empty dict if none set."""
    tk = _tags_key(env_key)
    if not backend.exists(tk):
        return {}
    raw = backend.download(tk)
    return json.loads(raw.decode())


def delete_tags(backend: BaseBackend, env_key: str) -> None:
    """Remove tags for the given env key (no-op if none exist)."""
    tk = _tags_key(env_key)
    if backend.exists(tk):
        backend.delete(tk)


def list_tagged(backend: BaseBackend, filter_tag: Optional[str] = None,
                filter_value: Optional[str] = None) -> List[str]:
    """Return env keys that have tags, optionally filtered by tag key/value."""
    all_keys = backend.list_keys()
    env_keys = [k for k in all_keys if not k.endswith(TAGS_SUFFIX)]
    results = []
    for ek in env_keys:
        tags = get_tags(backend, ek)
        if not tags:
            continue
        if filter_tag is not None:
            if filter_tag not in tags:
                continue
            if filter_value is not None and tags[filter_tag] != filter_value:
                continue
        results.append(ek)
    return results
