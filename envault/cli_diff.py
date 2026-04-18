"""CLI command for diffing two encrypted .env versions."""

import click
from .vault import Vault
from .diff import diff_envs
from .backends import get_backend


def _format_diff(changes: list[dict]) -> str:
    """Format diff changes into a human-readable string."""
    if not changes:
        return "No differences found."

    lines = []
    for change in changes:
        key = change["key"]
        kind = change["type"]
        if kind == "added":
            lines.append(click.style(f"+ {key}={change['new_value']}", fg="green"))
        elif kind == "removed":
            lines.append(click.style(f"- {key}={change['old_value']}", fg="red"))
        elif kind == "changed":
            lines.append(click.style(f"~ {key}: {change['old_value']} -> {change['new_value']}", fg="yellow"))
    return "\n".join(lines)


@click.command("diff")
@click.argument("key_a")
@click.argument("key_b")
@click.option("--passphrase", envvar="ENVAULT_PASSPHRASE", prompt=True, hide_input=True,
              help="Passphrase to decrypt both env versions.")
@click.option("--backend", "backend_type", default="local", show_default=True,
              type=click.Choice(["local", "s3"]), help="Storage backend.")
@click.option("--env-dir", default=".envault", show_default=True,
              help="Directory for local backend storage.")
@click.option("--s3-bucket", default=None, help="S3 bucket name (s3 backend only).")
@click.option("--s3-prefix", default="envault/", show_default=True,
              help="Key prefix for S3 objects.")
@click.pass_context
def diff(ctx, key_a, key_b, passphrase, backend_type, env_dir, s3_bucket, s3_prefix):
    """Show differences between two encrypted .env versions KEY_A and KEY_B."""
    try:
        backend = get_backend(
            backend_type,
            local_dir=env_dir,
            s3_bucket=s3_bucket,
            s3_prefix=s3_prefix,
        )
    except Exception as exc:
        raise click.ClickException(f"Failed to initialise backend: {exc}") from exc

    vault = Vault(backend=backend, passphrase=passphrase)

    try:
        content_a = vault.pull(key_a)
    except Exception as exc:
        raise click.ClickException(f"Could not pull '{key_a}': {exc}") from exc

    try:
        content_b = vault.pull(key_b)
    except Exception as exc:
        raise click.ClickException(f"Could not pull '{key_b}': {exc}") from exc

    changes = diff_envs(content_a, content_b)
    click.echo(f"Diff {key_a} -> {key_b}:")
    click.echo(_format_diff(changes))
