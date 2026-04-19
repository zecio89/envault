"""CLI command: envault watch — auto-push .env on file change."""
from __future__ import annotations

import click
from pathlib import Path

from envault.cli import make_vault
from envault.watch import watch_file


@click.group()
def watch() -> None:
    """Watch a .env file and auto-push changes."""


@watch.command("start")
@click.argument("env_file", type=click.Path(exists=True, dir_okay=False))
@click.option("--key", default=None, help="Vault key (defaults to filename stem).")
@click.option("--passphrase", prompt=True, hide_input=True)
@click.option("--backend", default="local", show_default=True)
@click.option("--backend-path", default=".envault", show_default=True)
@click.option("--interval", default=2.0, show_default=True, help="Poll interval (s).")
def start_cmd(
    env_file: str,
    key: str | None,
    passphrase: str,
    backend: str,
    backend_path: str,
    interval: float,
) -> None:
    """Watch ENV_FILE and push to vault whenever it changes."""
    path = Path(env_file)
    vault = make_vault(backend, backend_path, passphrase)
    env_key = key or path.stem

    click.echo(f"Watching {path} (key={env_key!r}) — Ctrl-C to stop.")

    def on_change(p: Path) -> None:
        vault.push(p, key=env_key)
        click.echo(f"[watch] pushed {p.name} → {env_key}")

    try:
        watch_file(path, on_change, interval=interval)
    except KeyboardInterrupt:
        click.echo("\nWatch stopped.")
