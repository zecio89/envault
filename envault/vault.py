"""High-level vault operations: push/pull encrypted .env files."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from envault.crypto import encrypt, decrypt
from envault.backends.base import BaseBackend


class Vault:
    """Wraps a backend with encrypt/decrypt operations for .env files."""

    def __init__(self, backend: BaseBackend, passphrase: str) -> None:
        self.backend = backend
        self.passphrase = passphrase

    def push(self, env_path: str | Path, key: Optional[str] = None) -> str:
        """Encrypt a .env file and upload it to the backend.

        Args:
            env_path: Path to the plaintext .env file.
            key: Storage key (defaults to the file's stem, e.g. ".env" -> ".env").

        Returns:
            The storage key used.
        """
        env_path = Path(env_path)
        if not env_path.exists():
            raise FileNotFoundError(f".env file not found: {env_path}")

        plaintext = env_path.read_text(encoding="utf-8")
        ciphertext = encrypt(plaintext, self.passphrase)

        storage_key = key or env_path.name
        self.backend.upload(storage_key, ciphertext.encode())
        return storage_key

    def pull(self, key: str, output_path: Optional[str | Path] = None) -> str:
        """Download and decrypt a .env file from the backend.

        Args:
            key: Storage key to retrieve.
            output_path: Where to write the decrypted content. If None, returns
                         the plaintext without writing.

        Returns:
            Decrypted plaintext content.
        """
        raw = self.backend.download(key)
        plaintext = decrypt(raw.decode(), self.passphrase)

        if output_path is not None:
            Path(output_path).write_text(plaintext, encoding="utf-8")

        return plaintext

    def list_envs(self) -> list[str]:
        """Return all stored env keys the backend."""
        return self.backend.list_keys()

    def delete_env(self, key: str) -> None:
        """Remove an env entry from the backend."""
        self.backend.delete(key)
