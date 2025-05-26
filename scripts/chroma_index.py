# chroma_index.py
import os
import chromadb
from chromadb.config import Settings

# Constants
SOURCE_DIR = "backend"
COLLECTION_NAME = "pynance-code"

# Embedded ChromaDB client (persisted locally)
client = chromadb.Client(
    Settings(persist_directory=".chroma_store", anonymized_telemetry=False)
)

collection = client.get_or_create_collection(name=COLLECTION_NAME)

# Load existing IDs to avoid duplicate work
existing_ids = set()
try:
    existing = collection.peek(limit=5000)
    existing_ids.update(existing["ids"])
except Exception:
    pass


def chunk_text(text, max_length=1000):
    return [text[i : i + max_length] for i in range(0, len(text), max_length)]


# Index .py, .md, and .txt files from source
count = 0
for root, _, files in os.walk(SOURCE_DIR):
    for filename in files:
        if filename.endswith((".py", ".md", ".txt")):
            path = os.path.join(root, filename)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            chunks = chunk_text(content)
            for i, chunk in enumerate(chunks):
                doc_id = f"{filename}-{i}"
                if doc_id in existing_ids:
                    continue  # Skip already indexed
                try:
                    collection.add(
                        documents=[chunk], metadatas=[{"source": path}], ids=[doc_id]
                    )
                    count += 1
                except chromadb.errors.IDAlreadyExistsError:
                    pass  # Extra safety: shouldn't hit if pre-checked

print(
    f"Indexed {count} new document chunks into ChromaDB collection '{COLLECTION_NAME}'."
)
print(f"Total documents: {collection.count()}")

