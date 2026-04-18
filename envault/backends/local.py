import os
from pathlib import Path

from envault.backends.base import BaseBackend


class LocalBackend(BaseBackend):
    """Stores encrypted env files on the local filesystem."""

    def __init__(self, storage_dir: str = ".envault"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def _key_path(self, key: str) -> Path:
        safe_key = key.replace("/", "__")
        return self.storage_dir / f"{safe_key}.enc"

    def upload(self, key: str, data: bytes) -> None:
        path = self._key_path(key)
        path.write_bytes(data)

    def download(self, key: str) -> bytes:
        path = self._key_path(key)
        if not path.exists():
            raise FileNotFoundError(f"Key '{key}' not found in local backend.")
        return path.read_bytes()

    def list_keys(self) -> list[str]:
        return [
            p.stem.replace("__", "/")
            for p in self.storage_dir.glob("*.enc")
        ]

    def delete(self, key: str) -> None:
        path = self._key_path(key)
        if not path.exists():
            raise FileNotFoundError(f"Key '{key}' not found in local backend.")
        path.unlink()

    def exists(self, key: str) -> bool:
        return self._key_path(key).exists()

    def rename(self, old_key: str, new_key: str) -> None:
        """Rename a stored key by moving its file to the new key path."""
        old_path = self._key_path(old_key)
        if not old_path.exists():
            raise FileNotFoundError(f"Key '{old_key}' not found in local backend.")
        new_path = self._key_path(new_key)
        if new_path.exists():
            raise FileExistsError(f"Key '{new_key}' already exists in local backend.")
        old_path.rename(new_path)
