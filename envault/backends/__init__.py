from envault.backends.base import BaseBackend
from envault.backends.local import LocalBackend
from envault.backends.s3 import S3Backend


def get_backend(backend_type: str, **kwargs) -> BaseBackend:
    """Factory function to instantiate a backend by type string.

    Args:
        backend_type: The type of backend to instantiate. Supported values
            are 'local' and 's3'.
        **kwargs: Additional keyword arguments passed to the backend constructor.

    Returns:
        An instantiated backend of the requested type.

    Raises:
        ValueError: If the given backend_type is not recognised.
    """
    backends = {
        "local": LocalBackend,
        "s3": S3Backend,
    }
    if backend_type not in backends:
        raise ValueError(
            f"Unknown backend '{backend_type}'. Choose from: {list(backends.keys())}"
        )
    return backends[backend_type](**kwargs)


def list_backends() -> list[str]:
    """Return the names of all available backend types."""
    return ["local", "s3"]


__all__ = ["BaseBackend", "LocalBackend", "S3Backend", "get_backend", "list_backends"]
