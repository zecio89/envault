"""Quota management: enforce per-backend limits on number of stored env keys."""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from typing import Optional

from envault.backends.base import BaseBackend

_QUOTA_KEY = "__envault__/quota.json"


@dataclass
class QuotaConfig:
    max_keys: int
    warn_threshold: float = 0.8  # fraction of max_keys at which to warn


@dataclass
class QuotaStatus:
    current: int
    max_keys: int
    warn_threshold: float

    @property
    def usage_fraction(self) -> float:
        if self.max_keys <= 0:
            return 0.0
        return self.current / self.max_keys

    @property
    def exceeded(self) -> bool:
        return self.current >= self.max_keys

    @property
    def warning(self) -> bool:
        return self.usage_fraction >= self.warn_threshold and not self.exceeded


def set_quota(backend: BaseBackend, max_keys: int, warn_threshold: float = 0.8) -> QuotaConfig:
    """Persist a quota configuration to the backend."""
    if max_keys < 1:
        raise ValueError("max_keys must be at least 1")
    if not (0.0 < warn_threshold <= 1.0):
        raise ValueError("warn_threshold must be between 0 (exclusive) and 1 (inclusive)")
    config = QuotaConfig(max_keys=max_keys, warn_threshold=warn_threshold)
    backend.upload(_QUOTA_KEY, json.dumps(asdict(config)).encode())
    return config


def get_quota(backend: BaseBackend) -> Optional[QuotaConfig]:
    """Retrieve the quota configuration, or None if not set."""
    if not backend.exists(_QUOTA_KEY):
        return None
    raw = backend.download(_QUOTA_KEY)
    data = json.loads(raw.decode())
    return QuotaConfig(**data)


def delete_quota(backend: BaseBackend) -> None:
    """Remove the quota configuration from the backend."""
    if backend.exists(_QUOTA_KEY):
        backend.delete(_QUOTA_KEY)


def check_quota(backend: BaseBackend) -> Optional[QuotaStatus]:
    """Return current quota status, or None if no quota is configured."""
    config = get_quota(backend)
    if config is None:
        return None
    all_keys = [k for k in backend.list_keys() if not k.startswith("__envault__/")]
    return QuotaStatus(
        current=len(all_keys),
        max_keys=config.max_keys,
        warn_threshold=config.warn_threshold,
    )


def enforce_quota(backend: BaseBackend) -> None:
    """Raise RuntimeError if the quota has been exceeded."""
    status = check_quota(backend)
    if status is not None and status.exceeded:
        raise RuntimeError(
            f"Quota exceeded: {status.current}/{status.max_keys} keys stored."
        )
