"""Vault: high-level encrypt/decrypt operations over a backend."""

from pathlib import Path
from typing import List, Optional

from envault.crypto import encrypt, decrypt
from envault.backends.base import BaseBackend
from envault import audit


class Vault:
    def __init__(self, backend: BaseBackend, passphrase: str):
        self.backend = backend
        self.passphrase = passphrase

    def push(
        self,
        env_file: Path,
        key: Optional[str] = None,
        audit_log: bool = True,
    ) -> str:
        """Encrypt and upload an env file. Returns the storage key."""
        plaintext = env_file.read_text()
        ciphertext = encrypt(plaintext, self.passphrase)
        storage_key = key or env_file.name
        self.backend.upload(storage_key, ciphertext)
        if audit_log:
            audit.log_event(
                "push",
                storage_key,
                backend=type(self.backend).__name__,
            )
        return storage_key

    def pull(
        self,
        key: str,
        output: Optional[Path] = None,
        audit_log: bool = True,
    ) -> str:
        """Download and decrypt an env file. Returns plaintext."""
        ciphertext = self.backend.download(key)
        plaintext = decrypt(ciphertext, self.passphrase)
        if output:
            output.write_text(plaintext)
        if audit_log:
            audit.log_event(
                "pull",
                key,
                backend=type(self.backend).__name__,
            )
        return plaintext

    def list_envs(self) -> List[str]:
        """List all keys stored in the backend."""
        return self.backend.list_keys()

    def delete(self, key: str, audit_log: bool = True) -> None:
        """Delete an env file from the backend."""
        self.backend.delete(key)
        if audit_log:
            audit.log_event(
                "delete",
                key,
                backend=type(self.backend).__name__,
            )
