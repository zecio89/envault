"""CLI command for exporting decrypted env files."""
from __future__ import annotations
import click
from envault.cli import make_vault
from envault.export import export_env, ExportFormat


@click.command("export")
@click.argument("key")
@click.option("--passphrase", envvar="ENVAULT_PASSPHRASE", prompt=True, hide_input=True)
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["dotenv", "json", "shell"]),
    default="dotenv",
    show_default=True,
    help="Output format.",
)
@click.option("--output", "-o", type=click.Path(), default=None, help="Write to file instead of stdout.")
@click.option("--backend", default="local", show_default=True)
@click.option("--env-dir", default=".envault", show_default=True)
@click.pass_context
def export(ctx: click.Context, key: str, passphrase: str, fmt: str, output: str | None, backend: str, env_dir: str) -> None:
    """Decrypt and export an env file in the chosen format."""
    vault = make_vault(backend, env_dir, passphrase)
    try:
        content = vault.pull(key)
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc
    result = export_env(content, fmt)  # type: ignore[arg-type]
    if output:
        with open(output, "w") as fh:
            fh.write(result)
        click.echo(f"Exported to {output}")
    else:
        click.echo(result)
