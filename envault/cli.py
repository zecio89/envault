"""CLI entry point for envault using Click."""
import sys
import click
from pathlib import Path

from envault.vault import Vault
from envault.backends import get_backend


def make_vault(backend_type: str, path_or_bucket: str, passphrase: str) -> Vault:
    backend = get_backend(backend_type, path_or_bucket)
    return Vault(backend=backend, passphrase=passphrase)


@click.group()
def cli():
    """envault — encrypt and manage .env files."""
    pass


@cli.command()
@click.argument("env_file", type=click.Path(exists=True))
@click.option("--key", default=None, help="Storage key name (default: filename)")
@click.option("--backend", default="local", show_default=True, help="Backend type: local or s3")
@click.option("--storage", required=True, help="Local path or S3 bucket name")
@click.option("--passphrase", envvar="ENVAULT_PASSPHRASE", prompt=True, hide_input=True)
def push(env_file, key, backend, storage, passphrase):
    """Encrypt and upload a .env file."""
    vault = make_vault(backend, storage, passphrase)
    stored_key = vault.push(Path(env_file), key=key)
    click.echo(f"Pushed to key: {stored_key}")


@cli.command()
@click.argument("key")
@click.option("--output", "-o", default=None, help="Output file path (default: <key>)")
@click.option("--backend", default="local", show_default=True, help="Backend type: local or s3")
@click.option("--storage", required=True, help="Local path or S3 bucket name")
@click.option("--passphrase", envvar="ENVAULT_PASSPHRASE", prompt=True, hide_input=True)
def pull(key, output, backend, storage, passphrase):
    """Download and decrypt a .env file."""
    vault = make_vault(backend, storage, passphrase)
    out_path = Path(output) if output else Path(key)
    vault.pull(key, out_path)
    click.echo(f"Pulled '{key}' -> {out_path}")


@cli.command(name="list")
@click.option("--backend", default="local", show_default=True, help="Backend type: local or s3")
@click.option("--storage", required=True, help="Local path or S3 bucket name")
@click.option("--passphrase", envvar="ENVAULT_PASSPHRASE", prompt=True, hide_input=True)
def list_envs(backend, storage, passphrase):
    """List all stored env keys."""
    vault = make_vault(backend, storage, passphrase)
    keys = vault.list_envs()
    if not keys:
        click.echo("No environments stored.")
    for k in keys:
        click.echo(f"  {k}")


@cli.command()
@click.argument("key")
@click.option("--backend", default="local", show_default=True, help="Backend type: local or s3")
@click.option("--storage", required=True, help="Local path or S3 bucket name")
@click.option("--passphrase", envvar="ENVAULT_PASSPHRASE", prompt=True, hide_input=True)
def delete(key, backend, storage, passphrase):
    """Delete a stored env by key."""
    vault = make_vault(backend, storage, passphrase)
    vault.backend.delete(key)
    click.echo(f"Deleted '{key}'")


if __name__ == "__main__":
    cli()
