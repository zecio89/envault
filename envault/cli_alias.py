"""CLI commands for alias management."""

import click
from envault.backends import get_backend
from envault.alias import set_alias, get_alias, delete_alias, list_aliases


@click.group()
def alias():
    """Manage friendly name aliases for env keys."""


def _backend(env_dir):
    return get_backend("local", root=env_dir)


@alias.command("set")
@click.argument("alias_name")
@click.argument("key")
@click.option("--env-dir", default=".", show_default=True)
def set_cmd(alias_name, key, env_dir):
    """Create or update an alias pointing to KEY."""
    try:
        result = set_alias(_backend(env_dir), alias_name, key)
        click.echo(f"Alias '{result['alias']}' -> '{result['key']}' saved.")
    except KeyError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@alias.command("get")
@click.argument("alias_name")
@click.option("--env-dir", default=".", show_default=True)
def get_cmd(alias_name, env_dir):
    """Show the key an alias points to."""
    key = get_alias(_backend(env_dir), alias_name)
    if key is None:
        click.echo(f"No alias found for '{alias_name}'.", err=True)
        raise SystemExit(1)
    click.echo(key)


@alias.command("rm")
@click.argument("alias_name")
@click.option("--env-dir", default=".", show_default=True)
def rm_cmd(alias_name, env_dir):
    """Remove an alias."""
    try:
        delete_alias(_backend(env_dir), alias_name)
        click.echo(f"Alias '{alias_name}' removed.")
    except KeyError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@alias.command("list")
@click.option("--env-dir", default=".", show_default=True)
def list_cmd(env_dir):
    """List all aliases."""
    aliases = list_aliases(_backend(env_dir))
    if not aliases:
        click.echo("No aliases defined.")
        return
    for a, k in sorted(aliases.items()):
        click.echo(f"{a} -> {k}")
