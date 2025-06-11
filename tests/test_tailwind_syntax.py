import re
from pathlib import Path

TAILWIND_PREFIXES = [
    "flex",
    "grid",
    "p-",
    "px-",
    "py-",
    "m-",
    "text-",
    "bg-",
    "rounded",
    "shadow",
    "gap-",
]

CLASS_PATTERN = re.compile(r'class="([^"]*)"')


def _collect_vue_files():
    base = Path(__file__).resolve().parents[1] / "frontend" / "src"
    return list(base.rglob("*.vue"))


def test_tailwind_classes_present():
    files = _collect_vue_files()
    assert files, "No Vue files found"
    found = 0
    for file in files:
        content = file.read_text()
        for match in CLASS_PATTERN.findall(content):
            if any(prefix in match for prefix in TAILWIND_PREFIXES):
                found += 1
                break
    assert found > 0, "No Tailwind CSS classes detected in Vue components"
