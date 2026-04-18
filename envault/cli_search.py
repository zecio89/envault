"""CLI commands for searching env keys and values."""
import click
from envault.cli import make_vault
from envault.search import search_keys


@click.group()
def search():
    """Search encrypted env keys and values."""


@search.command("run")
@click.argument("pattern")
@click.option("--env-dir", default=".envault", show_default=True)
@click.option("--passphrase", envvar="ENVAULT_PASSPHRASE", default=None,
              help="Passphrase to decrypt values (enables value search).")
@click.option("--values", is_flag=True, default=False,
              help="Also search inside decrypted values.")
def run_cmd(pattern, env_dir, passphrase, values):
    """Search for PATTERN in stored env keys (and optionally values)."""
    from envault.backends import get_backend
    backend = get_backend("local", root=env_dir)

    if values and not passphrase:
        raise click.UsageError("--passphrase is required when using --values")

    results = search_keys(backend, pattern, passphrase=passphrase, search_values=values)

    if not results:
        click.echo(f"No matches found for '{pattern}'.")
        return

    for r in results:
        key_label = click.style(r["key"], fg="cyan", bold=True)
        tag = " [key match]" if r["key_match"] else ""
        click.echo(f"{key_label}{tag}")
        for vm in r["value_matches"]:
            click.echo(f"  line {vm['line']}: {vm['content']}")
