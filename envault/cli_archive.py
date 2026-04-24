"""CLI commands for vault archiving."""

import click

from envault.archive import create_archive, delete_archive, list_archives, restore_archive
from envault.backends import get_backend


@click.group()
def archive():
    """Create and restore compressed vault archives."""


def _backend(env_dir: str):
    return get_backend("local", root=env_dir)


@archive.command("create")
@click.option("--env-dir", default=".envault", show_default=True, help="Vault storage directory.")
@click.option("--passphrase", prompt=True, hide_input=True, help="Vault passphrase.")
@click.option("--name", default=None, help="Archive label (default: timestamp).")
@click.option("--prefix", default="", help="Only archive keys with this prefix.")
def create_cmd(env_dir, passphrase, name, prefix):
    """Bundle all encrypted envs into a compressed archive."""
    backend = _backend(env_dir)
    try:
        meta = create_archive(backend, passphrase, name=name, prefix=prefix)
    except ValueError as exc:
        raise click.ClickException(str(exc))
    except Exception as exc:
        raise click.ClickException(f"Archive failed: {exc}")
    click.echo(f"Archive '{meta['name']}' created at {meta['created_at']}")
    click.echo(f"  Keys included: {len(meta['keys'])}")
    for k in meta["keys"]:
        click.echo(f"    {k}")


@archive.command("list")
@click.option("--env-dir", default=".envault", show_default=True)
def list_cmd(env_dir):
    """List all stored archives."""
    backend = _backend(env_dir)
    archives = list_archives(backend)
    if not archives:
        click.echo("No archives found.")
        return
    for meta in archives:
        key_count = len(meta.get("keys", []))
        click.echo(f"{meta['name']}  ({meta['created_at']})  [{key_count} keys]")


@archive.command("restore")
@click.argument("name")
@click.option("--env-dir", default=".envault", show_default=True)
@click.option("--overwrite", is_flag=True, default=False, help="Overwrite existing keys.")
def restore_cmd(env_dir, name, overwrite):
    """Restore envs from a named archive."""
    backend = _backend(env_dir)
    try:
        restored = restore_archive(backend, name, overwrite=overwrite)
    except KeyError as exc:
        raise click.ClickException(str(exc))
    if not restored:
        click.echo("Nothing restored (keys already exist; use --overwrite to force).")
        return
    click.echo(f"Restored {len(restored)} key(s) from archive '{name}':")
    for k in restored:
        click.echo(f"  {k}")


@archive.command("delete")
@click.argument("name")
@click.option("--env-dir", default=".envault", show_default=True)
@click.confirmation_option(prompt="Delete this archive?")
def delete_cmd(env_dir, name):
    """Delete a stored archive."""
    backend = _backend(env_dir)
    try:
        delete_archive(backend, name)
    except KeyError as exc:
        raise click.ClickException(str(exc))
    click.echo(f"Archive '{name}' deleted.")
