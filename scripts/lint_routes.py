"""Lint for disallowed top-level SQLAlchemy ``Model.query`` usage."""

import ast
import os
import sys
from pathlib import Path

VIOLATIONS: list[str] = []


def scan_file_for_top_level_query(filepath: str | Path) -> None:
    """Search ``filepath`` for top-level ``Model.query`` invocations."""
    path = Path(filepath).resolve()
    with path.open() as f:
        tree = ast.parse(f.read(), filename=str(path))

    for node in tree.body:
        if (
            isinstance(node, (ast.Assign, ast.Expr, ast.If))
            and ast.dump(node).find(".query") != -1
        ):
            VIOLATIONS.append(filepath)
            return


def main():
    for root, _, files in os.walk("app"):
        for file_name in files:
            if file_name.endswith(".py"):
                scan_file_for_top_level_query(Path(root) / file_name)

    if VIOLATIONS:
        print("[LINTER] ❌ Found top-level 'Model.query' usage in:")
        for path in VIOLATIONS:
            print(f" - {path}")
        sys.exit(1)
    else:
        print("[LINTER] ✅ No top-level 'Model.query' usage detected.")


if __name__ == "__main__":
    main()
