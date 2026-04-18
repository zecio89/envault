"""CLI sub-command for key rotation, registered onto the main cli group."""
import click

from envault.cli import make_vault, cli
from envault.rotate import rotate_key


@cli.command("rotate")
@click.option("--old-passphrase", prompt=True, hide_input=True, help="Current passphrase.")
@click.option("--new-passphrase", prompt=True, hide_input=True, confirmation_prompt=True,
              help="New passphrase.")
@click.option("--prefix", default="", show_default=True,
              help="Only rotate keys that start with this prefix.")
@click.option("--backend", "backend_type", default="local", show_default=True,
              type=click.Choice(["local", "s3"]), help="Storage backend.")
@click.option("--path", "backend_path", default=".envault", show_default=True,
              help="Local path or S3 bucket name.")
@click.pass_context
def rotate(ctx, old_passphrase, new_passphrase, prefix, backend_type, backend_path):
    """Re-encrypt all stored envs with a NEW passphrase."""
    vault = make_vault(backend_type, backend_path, old_passphrase)
    try:
        rotated = rotate_key(vault.backend, old_passphrase, new_passphrase, prefix=prefix)
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(f"Rotation failed: {exc}") from exc

    if rotated:
        click.echo(f"Rotated {len(rotated)} key(s):")
        for key in rotated:
            click.echo(f"  {key}")
    else:
        click.echo("Nothing to rotate.")
