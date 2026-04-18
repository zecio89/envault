"""CLI commands for env version history."""
import click
from envault.cli import make_vault
from envault.history import get_history, restore_version, clear_history
from envault.crypto import decrypt


@click.group("history")
def history():
    """Manage version history for env files."""


@history.command("log")
@click.argument("key")
@click.option("--env-dir", default=".", show_default=True)
@click.option("--backend", "backend_type", default="local", show_default=True)
@click.option("--s3-bucket", default=None)
def log_cmd(key, env_dir, backend_type, s3_bucket):
    """Show version history for KEY."""
    vault = make_vault(env_dir, backend_type, s3_bucket, passphrase="unused")
    entries = get_history(vault.backend, key)
    if not entries:
        click.echo(f"No history found for '{key}'.")
        return
    for e in entries:
        note = f"  # {e['note']}" if e.get("note") else ""
        click.echo(f"v{e['version']}  {e['timestamp']}  actor={e['actor']}{note}")


@history.command("restore")
@click.argument("key")
@click.argument("version", type=int)
@click.option("--passphrase", prompt=True, hide_input=True)
@click.option("--env-dir", default=".", show_default=True)
@click.option("--backend", "backend_type", default="local", show_default=True)
@click.option("--s3-bucket", default=None)
def restore_cmd(key, version, passphrase, env_dir, backend_type, s3_bucket):
    """Decrypt and print a specific VERSION of KEY."""
    vault = make_vault(env_dir, backend_type, s3_bucket, passphrase=passphrase)
    try:
        blob = restore_version(vault.backend, key, version)
    except KeyError as exc:
        raise click.ClickException(str(exc))
    try:
        plaintext = decrypt(blob, passphrase)
    except Exception:
        raise click.ClickException("Decryption failed — wrong passphrase?")
    click.echo(plaintext)


@history.command("clear")
@click.argument("key")
@click.option("--env-dir", default=".", show_default=True)
@click.option("--backend", "backend_type", default="local", show_default=True)
@click.option("--s3-bucket", default=None)
@click.confirmation_option(prompt="Clear all history for this key?")
def clear_cmd(key, env_dir, backend_type, s3_bucket):
    """Delete version history for KEY."""
    vault = make_vault(env_dir, backend_type, s3_bucket, passphrase="unused")
    clear_history(vault.backend, key)
    click.echo(f"History cleared for '{key}'.")
