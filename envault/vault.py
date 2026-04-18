"""Vault: high-level push/pull/list with optional history recording."""
from __future__ import annotations
from typing import List, Optional

from envault.crypto import encrypt, decrypt
from envault.backends.base import BaseBackend


class Vault:
    def __init__(self, backend: BaseBackend, passphrase: str) -> None:
        self.backend = backend
        self.passphrase = passphrase

    def push(
        self,
        plaintext: str,
        key: Optional[str] = None,
        actor: str = "unknown",
        note: str = "",
        track_history: bool = True,
    ) -> str:
        """Encrypt and upload plaintext; optionally record version history."""
        blob = encrypt(plaintext, self.passphrase)
        if key is None:
            import hashlib
            key = hashlib.sha256(blob.encode()).hexdigest()[:16]
        self.backend.upload(key, blob)
        if track_history:
            from envault.history import record_version
            record_version(self.backend, key, blob, actor=actor, note=note)
        return key

    def pull(self, key: str) -> str:
        """Download and decrypt the env stored at key."""
        blob = self.backend.download(key)
        return decrypt(blob, self.passphrase)

    def list_envs(self) -> List[str]:
        """List all non-metadata keys."""
        return [
            k for k in self.backend.list_keys()
            if not k.startswith(".")
        ]

    def delete(self, key: str) -> None:
        """Delete an env and its history."""
        from envault.history import clear_history
        self.backend.delete(key)
        clear_history(self.backend, key)
