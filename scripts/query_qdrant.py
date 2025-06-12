"""Query a Qdrant collection for semantically similar documents."""

import argparse

from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Query Qdrant for similar documents",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("query", nargs="+", help="Query text")
    parser.add_argument("--count", type=int, default=3, help="Results to return")
    parser.add_argument("--host", default="localhost", help="Qdrant host")
    parser.add_argument("--port", type=int, default=6333, help="Qdrant port")
    parser.add_argument("--collection", default="pynance-code", help="Collection name")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    query_text = " ".join(args.query)
    encoder = SentenceTransformer("all-MiniLM-L6-v2")
    vector = encoder.encode(query_text)

    client = QdrantClient(args.host, port=args.port)
    results = client.search(
        collection_name=args.collection, query_vector=vector, limit=args.count
    )

    print("\n[QDRANT] Search Results:\n")
    for i, r in enumerate(results, 1):
        preview = r.payload.get("docstring_summary") or str(r.payload)[:200]
        print(f"{i}. Score: {r.score:.3f}  →  {preview}")
        print(f"   └ Source: {r.payload.get('source', 'unknown')}\n")


if __name__ == "__main__":
    main()
