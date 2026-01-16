"""Utilities for safe path handling within the application."""

from pathlib import Path

from app.config import DIRECTORIES


def resolve_path(path: str | Path) -> Path:
    """Resolve ``path`` ensuring it stays within allowed directories."""
    candidate = Path(path).expanduser().resolve()
    allowed = [DIRECTORIES["DATA_DIR"].parent, *DIRECTORIES.values()]
    if not any(candidate.is_relative_to(base) for base in allowed):
        raise ValueError(f"{candidate} is outside allowed directories")
    return candidate


def resolve_data_path(path: str | Path) -> Path:
    """Resolve ``path`` within the configured data directory.

    Args:
        path: Relative or absolute file path to validate.

    Returns:
        A resolved ``Path`` that is guaranteed to live under ``DIRECTORIES["DATA_DIR"]``.

    Raises:
        ValueError: Raised if the resolved path is outside allowed directories.
    """
    candidate = Path(path).expanduser()
    if not candidate.is_absolute():
        candidate = DIRECTORIES["DATA_DIR"] / candidate
    return resolve_path(candidate)
