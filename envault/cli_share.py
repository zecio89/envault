"""CLI commands for sharing encrypted env blobs with other users."""
import click
from envault.cli import make_vault
from envault.share import share_env, retrieve_share, list_shares, delete_share
from envault.backends import get_backend


@click.group()
def share():
    """Share encrypted envs with other users."""


@share.command("send")
@click.argument("key")
@click.argument("users", nargs=-1, required=True)
@click.option("--passphrase", envvar="ENVAULT_PASSPHRASE", prompt=True, hide_input=True)
@click.option("--recipient-passphrase", prompt=True, hide_input=True)
@click.option("--actor", default="system", show_default=True)
@click.option("--env-dir", default=".", show_default=True)
def send_cmd(key, users, passphrase, recipient_passphrase, actor, env_dir):
    """Re-encrypt KEY for USERS under a new passphrase."""
    backend = get_backend(env_dir)
    try:
        share_key = share_env(backend, key, passphrase, recipient_passphrase, list(users), actor=actor)
        click.echo(f"Shared as: {share_key}")
    except (KeyError, PermissionError) as exc:
        raise click.ClickException(str(exc))


@share.command("receive")
@click.argument("key")
@click.argument("users", nargs=-1, required=True)
@click.option("--recipient-passphrase", prompt=True, hide_input=True)
@click.option("--env-dir", default=".", show_default=True)
def receive_cmd(key, users, recipient_passphrase, env_dir):
    """Retrieve and print a shared env blob."""
    backend = get_backend(env_dir)
    try:
        plaintext = retrieve_share(backend, key, list(users), recipient_passphrase)
        click.echo(plaintext)
    except KeyError as exc:
        raise click.ClickException(str(exc))


@share.command("list")
@click.argument("key")
@click.option("--env-dir", default=".", show_default=True)
def list_cmd(key, env_dir):
    """List all shares for KEY."""
    backend = get_backend(env_dir)
    shares = list_shares(backend, key)
    if not shares:
        click.echo("No shares found.")
    for s in shares:
        click.echo(s)


@share.command("delete")
@click.argument("key")
@click.argument("users", nargs=-1, required=True)
@click.option("--env-dir", default=".", show_default=True)
def delete_cmd(key, users, env_dir):
    """Delete a share entry for KEY and USERS."""
    backend = get_backend(env_dir)
    try:
        delete_share(backend, key, list(users))
        click.echo(f"Deleted share for {key} / {list(users)}.")
    except KeyError as exc:
        raise click.ClickException(str(exc))
