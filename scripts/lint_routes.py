# scripts/lint_routes.py
import os
import ast
import sys

VIOLATIONS = []


def scan_file_for_top_level_query(filepath):
    with open(filepath) as f:
        tree = ast.parse(f.read(), filename=filepath)

    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.Expr, ast.If)):
            if ast.dump(node).find(".query") != -1:
                VIOLATIONS.append(filepath)
                return


def main():
    for root, _, files in os.walk("app"):
        for f in files:
            if f.endswith(".py"):
                scan_file_for_top_level_query(os.path.join(root, f))

    if VIOLATIONS:
        print("[LINTER] ❌ Found top-level 'Model.query' usage in:")
        for path in VIOLATIONS:
            print(f" - {path}")
        sys.exit(1)
    else:
        print("[LINTER] ✅ No top-level 'Model.query' usage detected.")


if __name__ == "__main__":
    main()
