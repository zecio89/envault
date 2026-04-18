from envault.backends.base import BaseBackend
from envault.backends.local import LocalBackend
from envault.backends.s3 import S3Backend


def get_backend(backend_type: str, **kwargs) -> BaseBackend:
    """Factory function to instantiate a backend by type string."""
    backends = {
        "local": LocalBackend,
        "s3": S3Backend,
    }
    if backend_type not in backends:
        raise ValueError(
            f"Unknown backend '{backend_type}'. Choose from: {list(backends.keys())}"
        )
    return backends[backend_type](**kwargs)


__all__ = ["BaseBackend", "LocalBackend", "S3Backend", "get_backend"]
