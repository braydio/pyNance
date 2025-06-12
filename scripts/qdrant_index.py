"""Index project files into a Qdrant collection."""

import argparse
import os
import uuid

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.models import Distance, VectorParams
from sentence_transformers import SentenceTransformer
from chroma_support import chunk_text, extract_metadata

# Init encoder
encoder = SentenceTransformer("all-MiniLM-L6-v2")


def parse_args() -> argparse.Namespace:
    """Return CLI arguments."""

    parser = argparse.ArgumentParser(
        description="Index source files into Qdrant",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--reindex", action="store_true", help="Force full reindex")
    parser.add_argument("--source", default="backend", help="Source directory")
    parser.add_argument(
        "--host", default=os.getenv("QDRANT_HOST", "localhost"), help="Qdrant host"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("QDRANT_PORT", 6333)),
        help="Qdrant port",
    )
    parser.add_argument(
        "--collection",
        default=os.getenv("QDRANT_COLLECTION", "pynance-code"),
        help="Collection name",
    )
    return parser.parse_args()


EXCLUDE_DIRS = {".venv", "__pycache__"}


def main() -> None:
    args = parse_args()

    client = QdrantClient(args.host, port=args.port)
    if args.reindex:
        client.recreate_collection(
            collection_name=args.collection,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE),
        )
    else:
        client.get_or_create_collection(
            collection_name=args.collection,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE),
        )

    indexed_count = 0

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

                    metadata_base = extract_metadata(path, content)
                    chunks = chunk_text(content)

                    payloads, vectors, ids = [], [], []
                    for i, chunk in enumerate(chunks):
                        if not chunk.strip():
                            continue
                        doc_id = str(uuid.uuid4())
                        metadata = metadata_base.copy()
                        metadata.update({"chunk_index": i, "length": len(chunk)})
                        payloads.append(metadata)
                        vectors.append(encoder.encode(chunk))
                        ids.append(doc_id)

                    client.upsert(
                        collection_name=args.collection,
                        points=models.Batch(
                            ids=ids, vectors=vectors, payloads=payloads
                        ),
                    )
                    indexed_count += len(vectors)

                except Exception as e:
                    print(f"[QDRANT] Error processing file '{path}': {e}")

    print(f"[QDRANT] Indexed {indexed_count} vectors.")


if __name__ == "__main__":
    main()
