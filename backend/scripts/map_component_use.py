import os
import re
from collections import defaultdict

VIEWS_DIR = "frontend/src/views"
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


def normalize_component_name(path):
    return os.path.splitext(path)[0]  # strip .vue


def find_views():
    for root, _, files in os.walk(VIEWS_DIR):
        for name in files:
            if name.endswith(".vue"):
                yield os.path.join(root, name)


def map_usage():
    usage_map = defaultdict(list)
    component_names = [normalize_component_name(c) for c in COMPONENTS_TO_CHECK]

    for view_path in find_views():
        with open(view_path, encoding="utf-8") as f:
            content = f.read()

        for component in component_names:
            if re.search(rf"\b{re.escape(component)}\b", content):
                usage_map[component].append(view_path)

    return usage_map


if __name__ == "__main__":
    usage = map_usage()
    print("🔍 Component Usage by View:\n")
    for comp in COMPONENTS_TO_CHECK:
        base = normalize_component_name(comp)
        views = usage.get(base, [])
        if views:
            print(f"✅ `{comp}` used in:")
            for v in views:
                print(f"   • {v}")
        else:
            print(f"⚠️ `{comp}` appears unused in views/")
        print()
