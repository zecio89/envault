"""Register the policy command group into the main CLI.

Import this module in envault/cli.py (or setup.cfg entry_points) to attach
the `policy` subcommand group to the root `envault` CLI.

Example (cli.py)::

    from envault.cli_policy_group import attach_policy
    attach_policy(cli)
"""

from __future__ import annotations

import click

from envault.cli_policy import policy


def attach_policy(root: click.Group) -> None:
    """Attach the `policy` command group to *root*."""
    root.add_command(policy)


# ---------------------------------------------------------------------------
# Convenience: allow `python -m envault.cli_policy_group` for quick testing
# ---------------------------------------------------------------------------
if __name__ == "__main__":  # pragma: no cover
    policy()
