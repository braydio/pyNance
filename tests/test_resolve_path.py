import importlib.util
import os
import sys
import types

import pytest

# Stub config with directory constants
paths_module = os.path.join(
    os.path.dirname(__file__), "..", "backend", "app", "config", "paths.py"
)
spec_paths = importlib.util.spec_from_file_location("paths", paths_module)
paths = importlib.util.module_from_spec(spec_paths)
spec_paths.loader.exec_module(paths)

config_stub = types.ModuleType("app.config")
config_stub.DIRECTORIES = paths.DIRECTORIES
sys.modules["app.config"] = config_stub

MODULE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "backend", "app", "helpers", "path_utils.py"
)

spec = importlib.util.spec_from_file_location("path_utils", MODULE_PATH)
path_utils = importlib.util.module_from_spec(spec)
spec.loader.exec_module(path_utils)


def test_resolve_path_within_directories(tmp_path):
    target = path_utils.DIRECTORIES["TEMP_DIR"] / "example.json"
    resolved = path_utils.resolve_path(target)
    assert resolved == target.resolve()


def test_resolve_path_rejects_external(tmp_path):
    outside = tmp_path / "data.json"
    with pytest.raises(ValueError):
        path_utils.resolve_path(outside)
