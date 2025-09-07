"""Helpers for invoking the experimental Arbit CLI."""

from __future__ import annotations

import subprocess
from subprocess import CompletedProcess

ARBIT_CLI_PATH = "arbit/cli.py"


def _run(*args: str) -> CompletedProcess[str]:
    """Execute ``arbit/cli.py`` with the provided arguments.

    Args:
        *args: Arguments to pass to the CLI.

    Returns:
        The completed process with captured output.
    """
    cmd = ["python", ARBIT_CLI_PATH, *args]
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def start(threshold: float, fee: float) -> CompletedProcess[str]:
    """Start the Arbit process."""
    return _run("start", "--threshold", str(threshold), "--fee", str(fee))


def stop() -> CompletedProcess[str]:
    """Stop the Arbit process."""
    return _run("stop")


def update_config(threshold: float, fee: float) -> CompletedProcess[str]:
    """Update the Arbit configuration."""
    return _run("config", "update", "--threshold", str(threshold), "--fee", str(fee))
