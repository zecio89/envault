"""CLI commands for cloning env entries."""

from __future__ import annotations

import click

from envault.backends import get_backend
from envault.clone import clone_env


@click.group("clone")
def clone() -> None:
    """Clone an env entry to a new key or backend."""


@clone.command("run")
@click.argument("source_key")
@click.argument("dest_key")
@click.option("--passphrase", envvar="ENVAULT_PASSPHRASE", prompt=True, hide_input=True)
@click.option(
    "--new-passphrase",
    default=None,
    hide_input=True,
    help="Re-encrypt the clone with a different passphrase.",
)
@click.option("--env-dir", default=".envault", show_default=True)
@click.option(
    "--dest-dir",
    default=None,
    help="Destination backend directory (defaults to --env-dir).",
)
@click.option("--overwrite", is_flag=True, default=False, help="Overwrite existing dest key.")
def run_cmd(
    source_key: str,
    dest_key: str,
    passphrase: str,
    new_passphrase: str | None,
    env_dir: str,
    dest_dir: str | None,
    overwrite: bool,
) -> None:
    """Clone SOURCE_KEY to DEST_KEY."""
    src_backend = get_backend("local", path=env_dir)
    dst_backend = get_backend("local", path=dest_dir or env_dir)

    try:
        result = clone_env(
            src_backend,
            source_key,
            dst_backend,
            dest_key,
            passphrase,
            new_passphrase=new_passphrase or None,
            overwrite=overwrite,
        )
    except KeyError as exc:
        raise click.ClickException(str(exc)) from exc
    except FileExistsError as exc:
        raise click.ClickException(str(exc)) from exc

    reenc = " (re-encrypted)" if result["reencrypted"] else ""
    click.echo(f"Cloned {result['source_key']!r} -> {result['dest_key']!r}{reenc}")
