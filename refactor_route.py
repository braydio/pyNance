
import os
import re
import argparse
from pathlib import Path


def extract_route_func(file_path, identifier):
    with open(file_path, 'r') as f:
        code = f.read()

    # 1. Try matching by function name
    func_pattern = re.compile(
        rf'@.*?route\([^)]+\)\s+def {re.escape(identifier)}\(.*?\):.*?(?=^@|^def |\Z)',
        re.DOTALL | re.MULTILINE
    )
    match = func_pattern.search(code)
    if match:
        return match.group(0)

    # 2. Try matching by route string (e.g., "/generate_link_token")
    route_pattern = re.compile(
        rf'@.*?route\(["\']{re.escape(identifier)}["\'][^)]*\)\s+def (.*?)\(.*?\):.*?(?=^@|^def |\Z)',
        re.DOTALL | re.MULTILINE
    )
    match = route_pattern.search(code)
    if match:
        return match.group(0)

    return None


def find_vue_usages(route_path, vue_root="frontend/src"):
    matches = []
    route_pattern = re.compile(rf'(axios|fetch)\((\"|\'){re.escape(route_path)}(\"|\')')

    for root, _, files in os.walk(vue_root):
        for file in files:
            if file.endswith((".vue", ".js", ".ts")):
                full_path = os.path.join(root, file)
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    if route_pattern.search(content):
                        matches.append(full_path)
    return matches


def replace_in_file(file_path, old, new):
    with open(file_path, "r+", encoding="utf-8") as f:
        content = f.read()
        updated = content.replace(old, new)
        f.seek(0)
        f.write(updated)
        f.truncate()


def run_refactor(route_id, backend_file, vue_root="frontend/src"):
    route_code = extract_route_func(backend_file, route_id)
    if not route_code:
        print(f"\n❌ Could not find route `{route_id}` in {backend_file}\n")
        return

    print(f"\n✅ Found backend route for `{route_id}`:")
    print("-" * 60)
    print(route_code.strip())
    print("-" * 60)

    vue_usages = find_vue_usages(route_id, vue_root)
    if vue_usages:
        print(f"\n🔍 Found {len(vue_usages)} frontend usage(s) of `{route_id}`:")
        for path in vue_usages:
            print(f" - {path}")
    else:
        print("\n⚠️  No frontend usages found.")
        return

    confirm = input("\n✨ Do you want to replace this route in all frontend files? (y/N): ").strip().lower()
    if confirm == 'y':
        new_id = input("🔁 Enter the new route string to replace it with: ").strip()
        for path in vue_usages:
            replace_in_file(path, route_id, new_id)
            print(f"✏️ Updated: {path}")
        print("\n✅ All matched frontend usages have been updated.")
    else:
        print("\n🚫 Skipping replacement.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Refactor Flask route and linked frontend usages.")
    parser.add_argument("route_id", help="Flask route string (e.g., /generate_link_token) or function name")
    parser.add_argument("backend_file", help="Path to backend file containing the Flask route")
    parser.add_argument("--vue-root", default="frontend/src", help="Path to the Vue frontend source directory")

    args = parser.parse_args()
    run_refactor(args.route_id, args.backend_file, args.vue_root)

