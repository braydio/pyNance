# lint_routes.py
import os
import re
import sys


# Checks a line of code for route naming and verb/path conventions
def lint_pattern_complaint(line, filename):
    errors = []

    # Check for route-like patterns (e.g., @app.route("/api/..."))
    route_match = re.search(
        r"/(api|plaid|teller|transactions|accounts)/[a-zA-Z0-9_/]+", line
    )
    if route_match:
        route = route_match.group(0)

        # Enforce snake_case in route path
        if re.search(r"[A-Z]", route):
            errors.append(
                f"[Route Format] Path not snake_case → {filename}: {route.strip()}"
            )

        # Verb consistency checks
        if (
            ("get_" in route and not re.search(r"GET", line, re.IGNORECASE))
            or ("delete_" in route and not re.search(r"DELETE", line, re.IGNORECASE))
            or ("refresh_" in route and not re.search(r"POST", line, re.IGNORECASE))
        ):
            errors.append(
                f"[Verb Mismatch] Likely wrong HTTP verb in route → {filename}: {route.strip()}"
            )

    return errors


# Recursively walks all Python files and checks route violations
def check_files():
    violations = []
    ignore_dirs = {
        ".venv",
        "venv",
        ".git",
        "__pycache__",
        "node_modules",
        "site-packages",
    }

    for root, dirs, files in os.walk("."):
        # Skip ignored directories
        dirs[:] = [d for d in dirs if d not in ignore_dirs and not d.startswith(".")]

        for filename in files:
            if filename.endswith(".py"):
                filepath = os.path.join(root, filename)
                if any(ig in filepath for ig in ignore_dirs):
                    continue  # Skip if path includes ignored folder

                with open(filepath, "r", encoding="utf-8") as f:
                    for i, line in enumerate(f, 1):
                        errs = lint_pattern_complaint(line, filepath)
                        for err in errs:
                            violations.append(f"Line {i}: {err}")
    return violations


def main():
    errors = check_files()
    if errors:
        print("** LINTER VIOLATIONS: API Naming and Convention **")
        for error in errors:
            print(error)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
