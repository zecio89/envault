"""CLI command: envault compare."""
import click
from envault.cli import make_vault
from envault.compare import compare_envs


@click.group()
def compare():
    """Compare two stored env snapshots."""


@compare.command("run")
@click.argument("key_a")
@click.argument("key_b")
@click.option("--passphrase", "-p", envvar="ENVAULT_PASSPHRASE", prompt=True, hide_input=True)
@click.option("--passphrase-b", default=None, hide_input=True, help="Passphrase for key_b if different.")
@click.option("--env-dir", default=".envault", show_default=True)
def run_cmd(key_a, key_b, passphrase, passphrase_b, env_dir):
    """Compare KEY_A and KEY_B and print a summary."""
    from envault.backends import get_backend
    backend = get_backend("local", env_dir=env_dir)
    try:
        result = compare_envs(backend, key_a, key_b, passphrase, passphrase_b)
    except KeyError as exc:
        raise click.ClickException(str(exc))

    if result.only_in_a:
        click.echo(click.style(f"Only in {key_a}:", fg="yellow"))
        for k in result.only_in_a:
            click.echo(f"  - {k}")

    if result.only_in_b:
        click.echo(click.style(f"Only in {key_b}:", fg="yellow"))
        for k in result.only_in_b:
            click.echo(f"  + {k}")

    if result.different:
        click.echo(click.style("Different values:", fg="red"))
        for k in result.different:
            click.echo(f"  ~ {k}")

    if result.same:
        click.echo(click.style(f"Identical keys: {len(result.same)}", fg="green"))

    if not (result.only_in_a or result.only_in_b or result.different):
        click.echo(click.style("Environments are identical.", fg="green"))
