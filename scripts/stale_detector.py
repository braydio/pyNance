import os
import re

# Set your root directory for the frontend
FRONTEND_ROOT = "frontend/src"

# Components to verify
COMPONENTS_TO_CHECK = [
    "AccountsTableLite.vue",
    "LinkAccountFullProducts.vue",
    "UploadCSV.vue",
    "UploadDownloadCSV.vue",
    "RefreshControls.vue",
    "RefreshPlaidControls.vue",
    "RefreshTellerControls.vue",
    "TransactionsTable.vue",
    "UpdateTransactionsTable.vue",
]


def normalize_name(filename):
    return os.path.splitext(filename)[0]  # Strip .vue extension


def find_all_vue_sources():
    for root, _, files in os.walk(FRONTEND_ROOT):
        for name in files:
            if name.endswith(".vue") or name.endswith(".js") or name.endswith(".ts"):
                yield os.path.join(root, name)


def scan_usage():
    results = {}
    for component in COMPONENTS_TO_CHECK:
        base_name = normalize_name(component)
        usage_found = False

        pattern = re.compile(rf"\b{re.escape(base_name)}\b")
        for file in find_all_vue_sources():
            with open(file, encoding="utf-8") as f:
                content = f.read()
                if pattern.search(content):
                    usage_found = True
                    break

        results[component] = usage_found
    return results


if __name__ == "__main__":
    report = scan_usage()
    print("🔍 Component Usage Report:\n")
    for comp, used in report.items():
        status = "✅ USED" if used else "⚠️ UNUSED"
        print(f"{status:10} — {comp}")
