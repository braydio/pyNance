import os
import sys
import argparse
import chromadb
from chromadb.errors import ChromaError, IDAlreadyExistsError
from chroma_support import chunk_text, extract_metadata

# Argument parsing
parser = argparse.ArgumentParser(description="Index source files into ChromaDB")
parser.add_argument(
    "--reindex",
    action="store_true",
    help="Force full reindex, ignoring existing documents",
)
parser.add_argument(
    "--diff-only",
    action="store_true",
    help="Only add files not previously indexed (uses document ID cache)",
)
args = parser.parse_args()

# Configuration
SOURCE_DIR = "backend"
EXCLUDE_DIRS = {".venv", "__pycache__"}
DEFAULT_COLLECTION = os.getenv("CHROMA_COLLECTION", "pynance-code")
DEFAULT_HOST = os.getenv("CHROMA_HOST", "localhost")
DEFAULT_PORT = int(os.getenv("CHROMA_PORT", 8055))
DEFAULT_MODEL = os.getenv("CHROMA_MODEL", "all-MiniLM-L6-v2")

parser = argparse.ArgumentParser(description="Index project files into ChromaDB")
parser.add_argument("--source", default=SOURCE_DIR, help="Source directory")
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

# Existing ID tracking
existing_ids = set()
if not args.reindex:
    try:
        existing = collection.peek(limit=5000)
        existing_ids.update(existing["ids"])
        print(f"[CHROMA] Loaded {len(existing_ids)} existing document IDs")
    except ChromaError as e:
        print(f"[CHROMA] Warning: failed to peek collection: {e}")

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

                metadata_base = extract_metadata(path, content)
                chunks = chunk_text(content)

                for i, chunk in enumerate(chunks):
                    doc_id = f"{metadata_base['relative_path']}-{i}"

                    if not args.reindex:
                        if args.diff_only and doc_id in existing_ids:
                            continue
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
                print(f"[CHROMA] Error processing file '{path}': {e}")

print(
    f"[CHROMA] Indexed {indexed_count} new chunks into collection '{COLLECTION_NAME}'."
)

if indexed_count == 0:
    print("[CHROMA] No new documents were indexed.")
