"""Main CLI entry-point for envault."""
from __future__ import annotations

import click

from envault.backends import get_backend
from envault.vault import Vault


def make_vault(backend: str, backend_path: str, passphrase: str) -> Vault:
    b = get_backend(backend, backend_path)
    return Vault(b, passphrase)


@click.group()
def cli() -> None:
    """envault — encrypted .env manager."""


@cli.command()
@click.argument("env_file", type=click.Path(exists=True, dir_okay=False))
@click.option("--key", default=None)
@click.option("--passphrase", prompt=True, hide_input=True)
@click.option("--backend", default="local", show_default=True)
@click.option("--backend-path", default=".envault", show_default=True)
def push(env_file: str, key: str | None, passphrase: str, backend: str, backend_path: str) -> None:
    """Encrypt and push an .env file."""
    from pathlib import Path
    vault = make_vault(backend, backend_path, passphrase)
    stored_key = vault.push(Path(env_file), key=key)
    click.echo(f"Pushed → {stored_key}")


@cli.command()
@click.argument("key")
@click.argument("output", type=click.Path(dir_okay=False))
@click.option("--passphrase", prompt=True, hide_input=True)
@click.option("--backend", default="local", show_default=True)
@click.option("--backend-path", default=".envault", show_default=True)
def pull(key: str, output: str, passphrase: str, backend: str, backend_path: str) -> None:
    """Pull and decrypt an .env file."""
    from pathlib import Path
    vault = make_vault(backend, backend_path, passphrase)
    vault.pull(key, Path(output))
    click.echo(f"Pulled {key} → {output}")


@cli.command("list")
@click.option("--passphrase", prompt=True, hide_input=True)
@click.option("--backend", default="local", show_default=True)
@click.option("--backend-path", default=".envault", show_default=True)
def list_envs(passphrase: str, backend: str, backend_path: str) -> None:
    """List stored env keys."""
    vault = make_vault(backend, backend_path, passphrase)
    keys = vault.list_envs()
    if not keys:
        click.echo("(no envs stored)")
    else:
        for k in keys:
            click.echo(k)


# Register sub-command groups from other CLI modules
from envault.cli_watch import watch  # noqa: E402

cli.add_command(watch)
