"""Share encrypted env blobs with specific users via ACL-aware export."""
from __future__ import annotations

from typing import List, Optional

from envault.backends.base import BaseBackend
from envault.acl import get_acl, is_allowed
from envault.crypto import encrypt, decrypt


def share_env(
    backend: BaseBackend,
    key: str,
    old_passphrase: str,
    recipient_passphrase: str,
    users: List[str],
    actor: str = "system",
) -> str:
    """Re-encrypt an env blob under a recipient passphrase for a set of users.

    Raises PermissionError if actor is not in the ACL (when ACL is defined).
    Raises KeyError if the env key does not exist.
    Returns the share storage key where the re-encrypted blob is stored.
    """
    if not backend.exists(key):
        raise KeyError(f"Env '{key}' not found in backend.")

    allowed = is_allowed(backend, key, actor)
    if not allowed:
        raise PermissionError(f"Actor '{actor}' is not allowed to share '{key}'.")

    blob = backend.download(key)
    plaintext = decrypt(blob.decode(), old_passphrase)

    share_key = f"__shares__/{key}/{'+'.join(sorted(users))}"
    encrypted = encrypt(plaintext, recipient_passphrase)
    backend.upload(share_key, encrypted.encode())
    return share_key


def retrieve_share(
    backend: BaseBackend,
    key: str,
    users: List[str],
    recipient_passphrase: str,
) -> str:
    """Retrieve and decrypt a previously shared env blob.

    Returns the plaintext env content.
    """
    share_key = f"__shares__/{key}/{'+'.join(sorted(users))}"
    if not backend.exists(share_key):
        raise KeyError(f"No share found for key '{key}' and users {users}.")
    blob = backend.download(share_key)
    return decrypt(blob.decode(), recipient_passphrase)


def list_shares(backend: BaseBackend, key: str) -> List[str]:
    """List all share entries for a given env key."""
    prefix = f"__shares__/{key}/"
    return [k for k in backend.list_keys() if k.startswith(prefix)]


def delete_share(backend: BaseBackend, key: str, users: List[str]) -> None:
    """Delete a specific share entry."""
    share_key = f"__shares__/{key}/{'+'.join(sorted(users))}"
    if not backend.exists(share_key):
        raise KeyError(f"Share not found: {share_key}")
    backend.delete(share_key)
