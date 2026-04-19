"""CLI command: envault rename."""
from __future__ import annotations

import click

from envault.backends import get_backend
from envault.rename import rename_env


@click.group()
def rename():
    """Rename env keys."""


@rename.command("run")
@click.argument("old_key")
@click.argument("new_key")
@click.option("--passphrase", "-p", envvar="ENVAULT_PASSPHRASE", prompt=True, hide_input=True)
@click.option("--backend", "backend_type", default="local", show_default=True)
@click.option("--env-dir", default=".envault", show_default=True)
def run_cmd(old_key: str, new_key: str, passphrase: str, backend_type: str, env_dir: str):
    """Rename OLD_KEY to NEW_KEY in the backend."""
    backend = get_backend(backend_type, root=env_dir)
    try:
        result = rename_env(backend, old_key, new_key, passphrase)
        click.echo(f"Renamed {result['old_key']!r} -> {result['new_key']!r}")
    except KeyError as exc:
        raise click.ClickException(str(exc)) from exc
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
