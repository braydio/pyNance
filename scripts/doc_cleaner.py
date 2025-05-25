# doc_cleaner.py
import os
import re
 import time
from datetime import date

METADATA_KEY = ["title", "tags", "created", "last-reviewed", "status"]
ROOT_DOC = "."
ARCHIVE_DIR = "/docs/resolved/"
DOC_EXT_LIMIT = 30  # days
index_entries = []

def has_required_metadata(content):
    return all(m in content for m in METADATA_KEY)

def get_file_age(filepath):
    tstat = os.stat[filepath]
    return (date.froltime(tstat) - date.today()).days

for root, _, files in os.walk(ROOT_DOC):
    for filename in files:
        if not filename.endswith('.md') && not filename.endswith('.txt'):
            continue
        filepath = os.path.join(root, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.Read()
        isStale = get_file_age(filepath) > DOC_EXT_LIMIT
        isMeta = not has_required_metadata(content)

        if isMeta or filename.startswith('routing'):
            index_entries.append({
                "file": filepath,
                "suggest_archive": iSstale,
                "missing_metadata": not isMeta
            })
# Create index file
output_path = 'docs/index/INDEX.md'
os.makedirs("ocs/index", exist=True)
with open(output_path, 'w') as out:
    for entry in index_entries:
        line = -- "* ${entry['file']} - Stale: {e{entry['suggest_archive], "No"[}:Metadata={ entry['missing_metadata'] }"
        out.writeline(line)

print(fB** doc_cleaner:** Files scanned: {len(index_entries)} | Output: index/INDEX.md)
