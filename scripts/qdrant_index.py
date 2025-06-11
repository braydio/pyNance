# qdrant_index.py
import os
import sys
import argparse
import uuid
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.models import Distance, VectorParams
from chroma_support import chunk_text, extract_metadata
from sentence_transformers import SentenceTransformer

# Init encoder
encoder = SentenceTransformer("all-MiniLM-L6-v2")

parser = argparse.ArgumentParser(description="Index source files into Qdrant")
parser.add_argument("--reindex", action="store_true", help="Force full reindex")
args = parser.parse_args()

SOURCE_DIR = "backend"
EXCLUDE_DIRS = {".venv", "__pycache__"}
COLLECTION_NAME = "pynance-code"

client = QdrantClient("localhost", port=6333)
client.recreate_collection(
    collection_name=COLLECTION_NAME,
    vectors_config=VectorParams(size=384, distance=Distance.COSINE),
)

ids_indexed = set()
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

                payloads, vectors, ids = [], [], []
                for i, chunk in enumerate(chunks):
                    if not chunk.strip():
                        continue
                    doc_id = str(uuid.uuid4())  # Generate valid UUID
                    metadata = metadata_base.copy()
                    metadata.update({"chunk_index": i, "length": len(chunk)})
                    payloads.append(metadata)
                    vectors.append(encoder.encode(chunk))
                    ids.append(doc_id)
                    ids_indexed.add(doc_id)

                client.upsert(
                    collection_name=COLLECTION_NAME,
                    points=models.Batch(ids=ids, vectors=vectors, payloads=payloads),
                )
                indexed_count += len(vectors)

            except Exception as e:
                print(f"[QDRANT] Error processing file '{path}': {e}")

print(f"[QDRANT] Indexed {indexed_count} vectors.")
