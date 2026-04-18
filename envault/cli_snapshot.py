"""CLI commands for snapshot management."""
import click
from envault.cli import make_vault
from envault.snapshot import create_snapshot, list_snapshots, restore_snapshot, delete_snapshot


@click.group("snapshot")
def snapshot():
    """Manage full-environment snapshots."""


@snapshot.command("create")
@click.option("--dir", "env_dir", default=".", show_default=True)
@click.option("--passphrase", prompt=True, hide_input=True)
@click.option("--name", default=None, help="Snapshot name (auto-generated if omitted)")
def create_cmd(env_dir, passphrase, name):
    """Create a snapshot of all current environment keys."""
    vault = make_vault(env_dir, passphrase)
    try:
        result = create_snapshot(vault.backend, passphrase, name=name)
        click.echo(f"Snapshot '{result['name']}' created ({result['key_count']} keys).")
    except ValueError as e:
        raise click.ClickException(str(e))


@snapshot.command("list")
@click.option("--dir", "env_dir", default=".", show_default=True)
@click.option("--passphrase", prompt=True, hide_input=True)
def list_cmd(env_dir, passphrase):
    """List all available snapshots."""
    vault = make_vault(env_dir, passphrase)
    names = list_snapshots(vault.backend)
    if not names:
        click.echo("No snapshots found.")
    else:
        for n in names:
            click.echo(n)


@snapshot.command("restore")
@click.argument("name")
@click.option("--dir", "env_dir", default=".", show_default=True)
@click.option("--passphrase", prompt=True, hide_input=True)
def restore_cmd(name, env_dir, passphrase):
    """Restore all keys from a snapshot."""
    vault = make_vault(env_dir, passphrase)
    try:
        keys = restore_snapshot(vault.backend, name, passphrase)
        click.echo(f"Restored {len(keys)} keys from snapshot '{name}'.")
    except KeyError as e:
        raise click.ClickException(str(e))


@snapshot.command("delete")
@click.argument("name")
@click.option("--dir", "env_dir", default=".", show_default=True)
@click.option("--passphrase", prompt=True, hide_input=True)
def delete_cmd(name, env_dir, passphrase):
    """Delete a snapshot."""
    vault = make_vault(env_dir, passphrase)
    try:
        delete_snapshot(vault.backend, name)
        click.echo(f"Snapshot '{name}' deleted.")
    except KeyError as e:
        raise click.ClickException(str(e))
