# doc_cleaner.py
import os
from datetime import date

METADATA_KEYS = ["title", "tags", "created", "last-reviewed", "status"]
ROOT_DOC = "."
ARCHIVE_DIR = "docs/resolved/"
DOC_EXT_LIMIT = 30  # days
index_entries = []


def has_required_metadata(content):
    return all(k in content for k in METADATA_KEYS)


def get_file_age(filepath):
    tstat = os.stat(filepath).st_mtime
    file_date = date.fromtimestamp(tstat)
    return (date.today() - file_date).days


for root, _, files in os.walk(ROOT_DOC):
    for filename in files:
        if not (filename.endswith(".md") or filename.endswith(".txt")):
            continue
        filepath = os.path.join(root, filename)
        if ARCHIVE_DIR in filepath:
            continue  # skip already archived files

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        is_stale = get_file_age(filepath) > DOC_EXT_LIMIT
        is_meta_missing = not has_required_metadata(content)

        if is_meta_missing or filename.startswith("routing"):
            index_entries.append(
                {
                    "file": filepath,
                    "suggest_archive": is_stale,
                    "missing_metadata": is_meta_missing,
                }
            )

# Create index file
output_path = "docs/index/INDEX.md"
os.makedirs("docs/index", exist_ok=True)
with open(output_path, "w", encoding="utf-8") as out:
    for entry in index_entries:
        line = f"* {entry['file']} - Stale: {'Yes' if entry['suggest_archive'] else 'No'} | Metadata: {'Missing' if entry['missing_metadata'] else 'Present'}\n"
        out.write(line)

print(f"** doc_cleaner ** Files scanned: {len(index_entries)} | Output: {output_path}")
