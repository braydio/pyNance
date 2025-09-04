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
