# chroma_index.py
"""Index backend source files into a Chroma collection."""

import argparse
import os

import chromadb
from chromadb.errors import ChromaError, IDAlreadyExistsError
from chromadb.utils import embedding_functions

# Constants
DEFAULT_SOURCE = "backend"
EXCLUDE_DIRS = {".venv", "__pycache__"}
DEFAULT_COLLECTION = os.getenv("CHROMA_COLLECTION", "pynance-code")
DEFAULT_HOST = os.getenv("CHROMA_HOST", "localhost")
DEFAULT_PORT = int(os.getenv("CHROMA_PORT", 8055))
DEFAULT_MODEL = os.getenv("CHROMA_MODEL", "all-MiniLM-L6-v2")

parser = argparse.ArgumentParser(description="Index project files into ChromaDB")
parser.add_argument("--source", default=DEFAULT_SOURCE, help="Source directory")
parser.add_argument("--collection", default=DEFAULT_COLLECTION, help="Collection name")
parser.add_argument("--host", default=DEFAULT_HOST, help="ChromaDB host")
parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="ChromaDB port")
parser.add_argument("--model", default=DEFAULT_MODEL, help="SentenceTransformer model")
args = parser.parse_args()

print(f"[CHROMA] Connecting to http://{args.host}:{args.port}")
client = chromadb.HttpClient(host=args.host, port=args.port)
embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name=args.model
)
collection = client.get_or_create_collection(
    name=args.collection,
    embedding_function=embedding_fn,
)

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
for root, dirs, files in os.walk(args.source):
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
                relative_path = os.path.relpath(path, args.source)
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
    f"[CHROMA] Indexed {count} new document chunks into ChromaDB collection '{args.collection}'."
)
