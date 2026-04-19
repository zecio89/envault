"""CLI commands for merging two encrypted .env files."""

import click
from pathlib import Path

from envault.backends import get_backend
from envault.merge import merge_envs
from envault.vault import Vault


@click.group(name="merge")
def merge():
    """Merge two stored .env files into a destination key."""


@merge.command(name="run")
@click.argument("key_a")
@click.argument("key_b")
@click.argument("dest_key")
@click.option("--passphrase", "-p", required=True, help="Passphrase to decrypt both sources.")
@click.option("--dest-passphrase", default=None, help="Passphrase for destination (defaults to --passphrase).")
@click.option("--strategy", default="ours", show_default=True,
              type=click.Choice(["ours", "theirs"], case_sensitive=False),
              help="Conflict resolution strategy.")
@click.option("--env-dir", default=".envault", show_default=True,
              help="Local backend directory.")
def run_cmd(key_a, key_b, dest_key, passphrase, dest_passphrase, strategy, env_dir):
    """Merge KEY_A and KEY_B into DEST_KEY.

    Conflicts are resolved with --strategy (ours = keep KEY_A value,
    theirs = keep KEY_B value).
    """
    backend = get_backend("local", root=env_dir)
    dest_passphrase = dest_passphrase or passphrase

    vault_a = Vault(backend=backend, passphrase=passphrase)
    vault_b = Vault(backend=backend, passphrase=passphrase)

    blob_a = vault_a.pull(key_a)
    blob_b = vault_b.pull(key_b)

    result = merge_envs(
        blob_a.encode(),
        blob_b.encode(),
        strategy=strategy.lower(),
    )

    dest_vault = Vault(backend=backend, passphrase=dest_passphrase)
    dest_vault.push(result.merged.decode(), key=dest_key)

    click.echo(f"Merged '{key_a}' + '{key_b}' → '{dest_key}'")
    if result.added:
        click.echo(f"  Added keys   : {', '.join(sorted(result.added))}")
    if result.removed:
        click.echo(f"  Removed keys : {', '.join(sorted(result.removed))}")
    if result.conflicts:
        click.echo(
            f"  Conflicts ({strategy}): {', '.join(sorted(result.conflicts))}"
        )
    if not result.added and not result.removed and not result.conflicts:
        click.echo("  No differences found — files were identical.")
