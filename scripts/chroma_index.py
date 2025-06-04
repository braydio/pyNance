# chroma_index.py
import os
import chromadb
from chromadb.errors import ChromaError, IDAlreadyExistsError

# Constants
SOURCE_DIR = "backend"
EXCLUDE_DIRS = {".venv", "__pycache__"}
COLLECTION_NAME = "pynance-code"

print("[CHROMA] Connecting to Chroma server at http://localhost:8055")
client = chromadb.HttpClient(host="localhost", port=8055)
collection = client.get_or_create_collection(name=COLLECTION_NAME)

# Load existing IDs to avoid duplicate work
existing_ids = set()
try:
    existing = collection.peek(limit=5000)
    existing_ids.update(existing["ids"])
except ChromaError as e:
    print(f"[CHROMA] Warning: Failed to peek collection: {e}")


def chunk_text(text, max_length=1000):
    lines = text.splitlines()
    chunks, current, current_len = [], [], 0
    for line in lines:
        if current_len + len(line) > max_length:
            chunks.append("\n".join(current))
            current, current_len = [], 0
        current.append(line)
        current_len += len(line)
    if current:
        chunks.append("\n".join(current))
    return chunks


# Index .py, .md, and .txt files from source
count = 0
for root, dirs, files in os.walk(SOURCE_DIR):
    dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
    for filename in files:
        if filename.endswith((".py", ".md", ".txt")):
            path = os.path.join(root, filename)
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read().replace("\x00", "")
                if not content.strip():
                    continue

                chunks = chunk_text(content)
                relative_path = os.path.relpath(path, SOURCE_DIR)
                for i, chunk in enumerate(chunks):
                    doc_id = f"{relative_path}-{i}"
                    if doc_id in existing_ids:
                        continue
                    try:
                        collection.add(
                            documents=[chunk],
                            metadatas=[{"source": path}],
                            ids=[doc_id],
                        )
                        count += 1
                        if count % 50 == 0:
                            print(f"[CHROMA] Indexed {count} chunks so far...")
                    except IDAlreadyExistsError:
                        pass
            except Exception as e:
                print(f"[CHROMA] Error processing {path}: {e}")

print(
    f"[CHROMA] Indexed {count} new document chunks into ChromaDB collection '{COLLECTION_NAME}'."
)
