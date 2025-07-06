"""Index project source files into a ChromaDB collection."""

import argparse
import os

import chromadb
from chroma_support import chunk_text, extract_metadata
from chromadb.errors import ChromaError, IDAlreadyExistsError
from chromadb.utils import embedding_functions


def parse_args() -> argparse.Namespace:
    """Build and parse the CLI arguments."""

    parser = argparse.ArgumentParser(
        description="Index project files into ChromaDB",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--source", default="backend", help="Source directory")
    parser.add_argument(
        "--collection",
        default=os.getenv("CHROMA_COLLECTION", "pynance-code"),
        help="Collection name",
    )
    parser.add_argument(
        "--host", default=os.getenv("CHROMA_HOST", "localhost"), help="ChromaDB host"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("CHROMA_PORT", 8055)),
        help="ChromaDB port",
    )
    parser.add_argument(
        "--model",
        default=os.getenv("CHROMA_MODEL", "all-MiniLM-L6-v2"),
        help="SentenceTransformer model",
    )
    parser.add_argument("--reindex", action="store_true", help="Force full reindex")
    parser.add_argument(
        "--diff-only",
        action="store_true",
        help="Only add new files based on cached IDs",
    )
    return parser.parse_args()


EXCLUDE_DIRS = {".venv", "__pycache__"}


def main() -> None:
    args = parse_args()

    print(f"[CHROMA] Connecting to http://{args.host}:{args.port}")
    client = chromadb.HttpClient(host=args.host, port=args.port)
    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=args.model
    )
    collection = client.get_or_create_collection(
        name=args.collection, embedding_function=embedding_fn
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
                                print(
                                    f"[CHROMA] Indexed {indexed_count} chunks so far..."
                                )

                        except IDAlreadyExistsError:
                            continue

                except Exception as e:
                    print(f"[CHROMA] Error processing file '{path}': {e}")

    print(
        f"[CHROMA] Indexed {indexed_count} new chunks into collection '{args.collection}'."
    )

    if indexed_count == 0:
        print("[CHROMA] No new documents were indexed.")


if __name__ == "__main__":
    main()
