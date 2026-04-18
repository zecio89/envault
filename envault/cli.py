"""Main CLI entry point for envault."""
import click
from envault.vault import Vault
from envault.backends import get_backend


def make_vault(env_dir: str, passphrase: str) -> Vault:
    backend = get_backend(env_dir)
    return Vault(backend=backend, passphrase=passphrase)


@click.group()
def cli():
    """envault — encrypt and manage .env files."""


@cli.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("--dir", "env_dir", default=".", show_default=True)
@click.option("--passphrase", prompt=True, hide_input=True)
@click.option("--key", default=None)
def push(file, env_dir, passphrase, key):
    """Encrypt and push a .env file."""
    vault = make_vault(env_dir, passphrase)
    with open(file) as f:
        content = f.read()
    stored_key = vault.push(content, key=key)
    click.echo(f"Pushed as '{stored_key}'.")


@cli.command()
@click.argument("key")
@click.option("--dir", "env_dir", default=".", show_default=True)
@click.option("--passphrase", prompt=True, hide_input=True)
@click.option("--output", "-o", default=None)
def pull(key, env_dir, passphrase, output):
    """Decrypt and pull a .env file."""
    vault = make_vault(env_dir, passphrase)
    content = vault.pull(key)
    if output:
        with open(output, "w") as f:
            f.write(content)
        click.echo(f"Written to {output}.")
    else:
        click.echo(content)


@cli.command("list")
@click.option("--dir", "env_dir", default=".", show_default=True)
@click.option("--passphrase", prompt=True, hide_input=True)
def list_envs(env_dir, passphrase):
    """List stored environment keys."""
    vault = make_vault(env_dir, passphrase)
    keys = vault.list_envs()
    if not keys:
        click.echo("No environments stored.")
    else:
        for k in keys:
            click.echo(k)


# Register sub-command groups
from envault.cli_rotate import rotate  # noqa: E402
from envault.cli_diff import diff  # noqa: E402
from envault.cli_export import export  # noqa: E402
from envault.cli_tags import tags  # noqa: E402
from envault.cli_lock import lock  # noqa: E402
from envault.cli_history import history  # noqa: E402
from envault.cli_search import search  # noqa: E402
from envault.cli_snapshot import snapshot  # noqa: E402

cli.add_command(rotate)
cli.add_command(diff)
cli.add_command(export)
cli.add_command(tags)
cli.add_command(lock)
cli.add_command(history)
cli.add_command(search)
cli.add_command(snapshot)
