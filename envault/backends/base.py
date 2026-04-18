from abc import ABC, abstractmethod


class BaseBackend(ABC):
    """Abstract base class for envault storage backends."""

    @abstractmethod
    def upload(self, key: str, data: bytes) -> None:
        """Upload encrypted data to the backend."""
        ...

    @abstractmethod
    def download(self, key: str) -> bytes:
        """Download encrypted data from the backend."""
        ...

    @abstractmethod
    def list_keys(self) -> list[str]:
        """List all available keys in the backend."""
        ...

    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete a key from the backend."""
        ...

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if a key exists in the backend."""
        ...

    def upload_if_not_exists(self, key: str, data: bytes) -> bool:
        """Upload data only if the key does not already exist.

        Returns True if the data was uploaded, False if the key already existed.
        """
        if self.exists(key):
            return False
        self.upload(key, data)
        return True
