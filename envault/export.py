"""Export decrypted .env files to various formats."""
from __future__ import annotations
import json
from typing import Literal

ExportFormat = Literal["dotenv", "json", "shell"]


def _parse_env(content: str) -> dict[str, str]:
    pairs: dict[str, str] = {}
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        pairs[key.strip()] = value.strip()
    return pairs


def export_env(content: str, fmt: ExportFormat = "dotenv") -> str:
    """Convert decrypted env content to the requested format."""
    if fmt == "dotenv":
        return content
    pairs = _parse_env(content)
    if fmt == "json":
        return json.dumps(pairs, indent=2)
    if fmt == "shell":
        lines = [f'export {k}="{v}"' for k, v in pairs.items()]
        return "\n".join(lines)
    raise ValueError(f"Unknown format: {fmt}")
