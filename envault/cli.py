"""CLI entry point for envault."""

import click
from pathlib import Path

from envault.vault import Vault
from envault.backends import get_backend
from envault import audit


def make_vault(ctx: click.Context) -> Vault:
    backend = get_backend(ctx.obj["backend"], **ctx.obj.get("backend_opts", {}))
    return Vault(backend, ctx.obj["passphrase"])


@click.group()
@click.option("--passphrase", envvar="ENVAULT_PASSPHRASE", required=True, help="Encryption passphrase")
@click.option("--backend", default="local", show_default=True, help="Backend type: local or s3")
@click.option("--path", "backend_path", default=".envault-store", show_default=True)
@click.pass_context
def cli(ctx, passphrase, backend, backend_path):
    ctx.ensure_object(dict)
    ctx.obj["passphrase"] = passphrase
    ctx.obj["backend"] = backend
    ctx.obj["backend_opts"] = {"path": backend_path}


@cli.command()
@click.argument("env_file", type=click.Path(exists=True))
@click.option("--key", default=None, help="Override storage key")
@click.pass_context
def push(ctx, env_file, key):
    """Encrypt and upload an env file."""
    vault = make_vault(ctx)
    storage_key = vault.push(Path(env_file), key=key)
    click.echo(f"Pushed: {storage_key}")


@cli.command()
@click.argument("key")
@click.option("--output", "-o", default=None, type=click.Path(), help="Write plaintext to file")
@click.pass_context
def pull(ctx, key, output):
    """Download and decrypt an env file."""
    vault = make_vault(ctx)
    plaintext = vault.pull(key, output=Path(output) if output else None)
    if not output:
        click.echo(plaintext)


@cli.command(name="list")
@click.pass_context
def list_envs(ctx):
    """List stored env keys."""
    vault = make_vault(ctx)
    keys = vault.list_envs()
    if not keys:
        click.echo("No envs stored.")
    for k in keys:
        click.echo(k)


@cli.command()
@click.argument("key")
@click.pass_context
def delete(ctx, key):
    """Delete a stored env by key."""
    vault = make_vault(ctx)
    vault.delete(key)
    click.echo(f"Deleted: {key}")


@cli.command(name="audit-log")
@click.option("--clear", is_flag=True, help="Clear the audit log")
def audit_log(clear):
    """View or clear the audit log."""
    if clear:
        audit.clear_log()
        click.echo("Audit log cleared.")
        return
    events = audit.read_events()
    if not events:
        click.echo("No audit events found.")
        return
    for e in events:
        click.echo(f"{e['timestamp']}  {e['action']:8s}  {e['key']}  ({e['user']} via {e['backend']})")
