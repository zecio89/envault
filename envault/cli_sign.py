"""CLI commands for signing and verifying env blobs."""
from __future__ import annotations

import click

from envault.backends import get_backend
from envault.sign import delete_signature, get_signature, list_signed, sign_env, verify_signature


def _backend(env_dir: str):
    return get_backend("local", root=env_dir)


@click.group()
def sign():
    """Sign and verify env blobs with an HMAC secret."""


@sign.command("sign")
@click.argument("key")
@click.option("--secret", required=True, envvar="ENVAULT_SIGN_SECRET", help="HMAC secret")
@click.option("--env-dir", default=".envault", show_default=True)
def sign_cmd(key: str, secret: str, env_dir: str):
    """Compute and store an HMAC signature for KEY."""
    backend = _backend(env_dir)
    try:
        record = sign_env(backend, key, secret)
    except KeyError as exc:
        raise click.ClickException(str(exc))
    click.echo(f"Signed {key!r}  digest={record['digest'][:16]}...")


@sign.command("verify")
@click.argument("key")
@click.option("--secret", required=True, envvar="ENVAULT_SIGN_SECRET", help="HMAC secret")
@click.option("--env-dir", default=".envault", show_default=True)
def verify_cmd(key: str, secret: str, env_dir: str):
    """Verify the HMAC signature of KEY."""
    backend = _backend(env_dir)
    try:
        ok = verify_signature(backend, key, secret)
    except KeyError as exc:
        raise click.ClickException(str(exc))
    if ok:
        click.echo(f"OK  {key!r} signature is valid.")
    else:
        click.echo(f"FAIL  {key!r} signature is missing or invalid.", err=True)
        raise SystemExit(1)


@sign.command("show")
@click.argument("key")
@click.option("--env-dir", default=".envault", show_default=True)
def show_cmd(key: str, env_dir: str):
    """Show the stored signature record for KEY."""
    backend = _backend(env_dir)
    record = get_signature(backend, key)
    if record is None:
        click.echo(f"No signature stored for {key!r}.")
    else:
        click.echo(f"key       : {record['env_key']}")
        click.echo(f"algorithm : {record['algorithm']}")
        click.echo(f"digest    : {record['digest']}")


@sign.command("rm")
@click.argument("key")
@click.option("--env-dir", default=".envault", show_default=True)
def rm_cmd(key: str, env_dir: str):
    """Delete the stored signature for KEY."""
    backend = _backend(env_dir)
    removed = delete_signature(backend, key)
    if removed:
        click.echo(f"Signature for {key!r} removed.")
    else:
        click.echo(f"No signature found for {key!r}.")


@sign.command("list")
@click.option("--env-dir", default=".envault", show_default=True)
def list_cmd(env_dir: str):
    """List all env keys that have a stored signature."""
    backend = _backend(env_dir)
    keys = list_signed(backend)
    if not keys:
        click.echo("No signed keys.")
    else:
        for k in sorted(keys):
            click.echo(k)
