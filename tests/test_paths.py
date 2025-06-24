"""Tests for backend path configuration."""

import importlib.util
import os
from pathlib import Path

MODULE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "backend", "app", "config", "paths.py"
)


def test_directories_created(tmp_path):
    """Ensure directories are created when the module is imported."""
    # Prepare a temp copy of the module with BASE_DIR pointing to tmp_path
    module_text = Path(MODULE_PATH).read_text(encoding="utf-8")
    replacement = f"BASE_DIR = Path('{tmp_path}')"
    module_text = module_text.replace(
        "BASE_DIR = Path(__file__).resolve().parent.parent", replacement
    )
    temp_module = tmp_path / "paths_temp.py"
    temp_module.write_text(module_text, encoding="utf-8")

    spec = importlib.util.spec_from_file_location("paths_temp", temp_module)
    paths = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(paths)

    for path in paths.DIRECTORIES.values():
        assert path.exists() and path.is_dir()
