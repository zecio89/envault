"""Search across encrypted env keys and metadata."""
from __future__ import annotations
from typing import Optional
from envault.backends.base import BaseBackend
from envault.crypto import decrypt


def search_keys(
    backend: BaseBackend,
    pattern: str,
    passphrase: Optional[str] = None,
    search_values: bool = False,
) -> list[dict]:
    """Search env keys (and optionally decrypted values) for a pattern.

    Args:
        backend: storage backend to search
        pattern: substring to match (case-insensitive)
        passphrase: required when search_values=True
        search_values: if True, also decrypt and search values

    Returns:
        List of dicts with 'key' and optionally 'matches' list.
    """
    if search_values and passphrase is None:
        raise ValueError("passphrase is required when search_values=True")

    pattern_lower = pattern.lower()
    results = []

    for key in backend.list_keys():
        match_info: dict = {"key": key, "key_match": False, "value_matches": []}

        if pattern_lower in key.lower():
            match_info["key_match"] = True

        if search_values:
            blob = backend.download(key)
            plaintext = decrypt(blob.decode(), passphrase)  # type: ignore[arg-type]
            for i, line in enumerate(plaintext.splitlines(), 1):
                if pattern_lower in line.lower():
                    match_info["value_matches"].append({"line": i, "content": line})

        if match_info["key_match"] or match_info["value_matches"]:
            results.append(match_info)

    return results
