import os
import difflib

COMPONENTS_DIR = "frontend/src/components"
EXTENSIONS = {".vue"}
SIZE_TOLERANCE = 10  # Bytes


def get_vue_files(base):
    for root, _, files in os.walk(base):
        for f in files:
            if os.path.splitext(f)[1] in EXTENSIONS:
                path = os.path.join(root, f)
                yield path


def is_similar(name1, name2):
    return difflib.SequenceMatcher(None, name1, name2).ratio() > 0.75


def read_file(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def detect_duplicates():
    files = list(get_vue_files(COMPONENTS_DIR))
    possible_dupes = []

    for i, file1 in enumerate(files):
        name1 = os.path.basename(file1)
        size1 = os.path.getsize(file1)
        for j, file2 in enumerate(files):
            if i >= j:
                continue
            name2 = os.path.basename(file2)
            size2 = os.path.getsize(file2)

            if abs(size1 - size2) <= SIZE_TOLERANCE and is_similar(name1, name2):
                content1 = read_file(file1)
                content2 = read_file(file2)

                if content1.strip() == content2.strip():
                    match_type = "🟢 IDENTICAL"
                else:
                    match_type = "🟡 SIMILAR"

                possible_dupes.append((file1, file2, match_type))

    if possible_dupes:
        print("🔍 Potential duplicate Vue components:\n")
        for file1, file2, status in possible_dupes:
            print(f"{status}\n - {file1}\n - {file2}\n")
    else:
        print("✅ No duplicates found.")


if __name__ == "__main__":
    detect_duplicates()
