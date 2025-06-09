import os
import chromadb
from chromadb.errors import ChromaError, IDAlreadyExistsError
from chroma_support import chunk_text, extract_metadata

# Configuration
SOURCE_DIR = "backend"
EXCLUDE_DIRS = {".venv", "__pycache__"}
COLLECTION_NAME = "pynance-code"

print("[CHROMA] Connecting to Chroma server at http://localhost:8055")
client = chromadb.HttpClient(host="localhost", port=8055)
collection = client.get_or_create_collection(name=COLLECTION_NAME)

# Preload existing document IDs to avoid duplicate insertion
existing_ids = set()
try:
    existing = collection.peek(limit=5000)
    existing_ids.update(existing["ids"])
except ChromaError as e:
    print(f"[CHROMA] Warning: Failed to peek collection: {e}")

indexed_count = 0

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

                # Enrich metadata for each file
                metadata_base = extract_metadata(path, content)
                chunks = chunk_text(content)

                for i, chunk in enumerate(chunks):
                    doc_id = f"{metadata_base['relative_path']}-{i}"
                    if doc_id in existing_ids:
                        continue

                    metadata = metadata_base.copy()
                    metadata["chunk_index"] = i
                    metadata["length"] = len(chunk)

                    try:
                        collection.add(
                            documents=[chunk],
                            metadatas=[metadata],
                            ids=[doc_id],
                        )
                        indexed_count += 1
                        if indexed_count % 50 == 0:
                            print(f"[CHROMA] Indexed {indexed_count} chunks so far...")

                    except IDAlreadyExistsError:
                        continue

            except Exception as e:
                print(f"[CHROMA] Error indexing file {path}: {e}")

print(
    f"[CHROMA] Indexed {indexed_count} new document chunks into collection '{COLLECTION_NAME}'."
)
