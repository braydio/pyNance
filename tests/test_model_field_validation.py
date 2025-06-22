"""Validate model attribute usage in routes and helpers."""

import pytest

# Skip this test suite entirely if Flask-SQLAlchemy is missing.  Pre-commit
# environments may lack optional dependencies, and this check avoids import
# errors during collection.
pytest.importorskip("flask_sqlalchemy")

# pylint: disable=import-error

import ast
import importlib.util
import os
import sys
import types

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.inspection import inspect as sa_inspect

BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "backend")


def _load_models():
    """Load backend models with minimal Flask-SQLAlchemy context."""
    sys.modules.pop("app", None)
    app_pkg = types.ModuleType("app")
    extensions_stub = types.ModuleType("app.extensions")
    extensions_stub.db = SQLAlchemy()
    app_pkg.extensions = extensions_stub
    sys.modules["app"] = app_pkg
    sys.modules["app.extensions"] = extensions_stub

    module_path = os.path.join(BASE_DIR, "app", "models.py")
    spec = importlib.util.spec_from_file_location("app.models", module_path)
    models = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(models)
    return models


def _collect_model_fields(models):
    fields = {}
    for name in dir(models):
        obj = getattr(models, name)
        if isinstance(obj, type) and getattr(obj, "__tablename__", None):
            attrs = {prop.key for prop in sa_inspect(obj).attrs}
            attrs.update({"query", "query_class"})
            fields[name] = attrs
    return fields


def _parse_import_aliases(tree, valid):
    alias_map = {}
    alias_pkg = {}
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == "app.models":
            for alias in node.names:
                if alias.name in valid:
                    alias_map[alias.asname or alias.name] = alias.name
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "app.models":
                    alias_pkg[alias.asname or alias.name] = alias.name
    return alias_map, alias_pkg


def _find_invalid_accesses(path, valid):
    with open(path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=path)
    alias_map, alias_pkg = _parse_import_aliases(tree, valid)
    violations = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            if isinstance(node.value, ast.Name):
                base = node.value.id
                model_name = alias_map.get(base)
                if model_name and node.attr not in valid.get(model_name, set()):
                    violations.append(f"{path}:{node.lineno} {model_name}.{node.attr}")
            elif isinstance(node.value, ast.Attribute):
                inner = node.value
                if isinstance(inner.value, ast.Name):
                    pkg = alias_pkg.get(inner.value.id)
                    model_name = inner.attr
                    if (
                        pkg
                        and model_name in valid
                        and node.attr not in valid[model_name]
                    ):
                        violations.append(
                            f"{path}:{node.lineno} {model_name}.{node.attr}"
                        )
    return violations


def _collect_py_files():
    targets = [
        os.path.join(BASE_DIR, "app", "routes"),
        os.path.join(BASE_DIR, "app", "helpers"),
    ]
    files = []
    for target in targets:
        for root, _, filenames in os.walk(target):
            for name in filenames:
                if name.endswith(".py") and not name.startswith("__"):
                    files.append(os.path.join(root, name))
    return files


def test_model_fields_are_valid():
    """Ensure all model attributes referenced in code actually exist."""
    models = _load_models()
    valid = _collect_model_fields(models)
    violations = []
    for file in _collect_py_files():
        violations.extend(_find_invalid_accesses(file, valid))
    assert not violations, "Invalid model field access found:\n" + "\n".join(violations)
