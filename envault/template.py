"""Template rendering: substitute .env values into a template file."""
from __future__ import annotations

import re
from typing import Optional

from envault.backends.base import BaseBackend
from envault.crypto import decrypt

_VAR_RE = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")


def _parse_env(blob: str) -> dict[str, str]:
    """Parse decrypted env blob into a key/value dict."""
    result: dict[str, str] = {}
    for line in blob.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, _, v = line.partition("=")
            result[k.strip()] = v.strip()
    return result


def list_template_vars(template: str) -> list[str]:
    """Return a sorted list of unique variable names referenced in *template*.

    Useful for validating that all required variables are present in an env
    before attempting a full render.

    Example::

        >>> list_template_vars("Hello {{ NAME }}, your token is {{ TOKEN }}")
        ['NAME', 'TOKEN']
    """
    return sorted(set(_VAR_RE.findall(template)))


def render_template(
    template: str,
    backend: BaseBackend,
    env_key: str,
    passphrase: str,
    missing_ok: bool = False,
) -> str:
    """Render *template* by substituting ``{{ VAR }}`` placeholders.

    Values are sourced from the encrypted env stored at *env_key*.
    If *missing_ok* is False (default) a KeyError is raised for unknown vars.
    """
    blob = backend.download(env_key)
    if blob is None:
        raise FileNotFoundError(f"env key not found in backend: {env_key}")
    plaintext = decrypt(blob.decode(), passphrase)
    env_vars = _parse_env(plaintext)

    def replacer(match: re.Match) -> str:
        name = match.group(1)
        if name not in env_vars:
            if missing_ok:
                return match.group(0)
            raise KeyError(f"Variable '{name}' not found in env '{env_key}'")
        return env_vars[name]

    return _VAR_RE.sub(replacer, template)
