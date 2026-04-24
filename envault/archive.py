"""Archive and restore entire vault snapshots as a single compressed bundle."""

import io
import json
import tarfile
from datetime import datetime, timezone
from typing import Optional

from envault.backends.base import BaseBackend


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _archive_key(name: str) -> str:
    return f"__archives__/{name}.tar.gz"


def create_archive(
    backend: BaseBackend,
    passphrase: str,
    name: Optional[str] = None,
    prefix: str = "",
) -> dict:
    """Bundle all encrypted env blobs into a gzipped tar archive stored in the backend.

    Args:
        backend: storage backend to read from and write to.
        passphrase: used only to verify blobs are readable (not re-encrypted).
        name: archive label; defaults to ISO timestamp slug.
        prefix: optional key prefix filter (e.g. 'prod/').

    Returns:
        Metadata dict with name, created_at, and included keys.
    """
    from envault.crypto import decrypt

    all_keys = [k for k in backend.list_keys() if not k.startswith("__")]
    if prefix:
        all_keys = [k for k in all_keys if k.startswith(prefix)]

    if not all_keys:
        raise ValueError("No env keys found to archive.")

    # Verify all blobs are decryptable before archiving
    for key in all_keys:
        blob = backend.download(key)
        decrypt(blob, passphrase)  # raises on bad passphrase

    name = name or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    created_at = _now_iso()

    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        manifest = {"name": name, "created_at": created_at, "keys": all_keys}
        manifest_bytes = json.dumps(manifest).encode()
        info = tarfile.TarInfo(name="manifest.json")
        info.size = len(manifest_bytes)
        tar.addfile(info, io.BytesIO(manifest_bytes))

        for key in all_keys:
            blob = backend.download(key)
            blob_bytes = blob.encode() if isinstance(blob, str) else blob
            info = tarfile.TarInfo(name=key)
            info.size = len(blob_bytes)
            tar.addfile(info, io.BytesIO(blob_bytes))

    backend.upload(_archive_key(name), buf.getvalue().decode("latin-1"))
    return manifest


def list_archives(backend: BaseBackend) -> list:
    """Return metadata for all stored archives."""
    results = []
    for key in backend.list_keys():
        if key.startswith("__archives__/") and key.endswith(".tar.gz"):
            raw = backend.download(key)
            buf = io.BytesIO(raw.encode("latin-1"))
            with tarfile.open(fileobj=buf, mode="r:gz") as tar:
                member = tar.getmember("manifest.json")
                manifest = json.load(tar.extractfile(member))
            results.append(manifest)
    return sorted(results, key=lambda m: m["created_at"])


def restore_archive(
    backend: BaseBackend,
    name: str,
    overwrite: bool = False,
) -> list:
    """Restore all env blobs from a named archive back into the backend.

    Returns list of restored keys.
    """
    raw = backend.download(_archive_key(name))
    buf = io.BytesIO(raw.encode("latin-1"))
    restored = []
    with tarfile.open(fileobj=buf, mode="r:gz") as tar:
        for member in tar.getmembers():
            if member.name == "manifest.json":
                continue
            if not overwrite and backend.exists(member.name):
                continue
            blob = tar.extractfile(member).read().decode()
            backend.upload(member.name, blob)
            restored.append(member.name)
    return restored


def delete_archive(backend: BaseBackend, name: str) -> None:
    """Remove a stored archive from the backend."""
    key = _archive_key(name)
    if not backend.exists(key):
        raise KeyError(f"Archive '{name}' not found.")
    backend.delete(key)
