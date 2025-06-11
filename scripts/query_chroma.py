# scripts/query_chroma.py

"""Query a Chroma collection for semantically similar documents."""

import argparse
import os
import sys

import chromadb
from chromadb.errors import ChromaError
from chromadb.utils import embedding_functions

DEFAULT_COLLECTION = os.getenv("CHROMA_COLLECTION", "pynance-code")
DEFAULT_COUNT = int(os.getenv("CHROMA_RESULT_COUNT", 3))
DEFAULT_HOST = os.getenv("CHROMA_HOST", "localhost")
DEFAULT_PORT = int(os.getenv("CHROMA_PORT", 8055))
DEFAULT_MODEL = os.getenv("CHROMA_MODEL", "all-MiniLM-L6-v2")

parser = argparse.ArgumentParser(description="Query ChromaDB for similar documents.")
parser.add_argument("query", nargs="+", help="Query text")
parser.add_argument(
    "-n", "--count", type=int, default=DEFAULT_COUNT, help="Number of results to return"
)
parser.add_argument("--collection", default=DEFAULT_COLLECTION, help="Collection name")
parser.add_argument("--host", default=DEFAULT_HOST, help="ChromaDB host")
parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="ChromaDB port")
parser.add_argument("--model", default=DEFAULT_MODEL, help="SentenceTransformer model")
parser.add_argument(
    "--show-distance", action="store_true", help="Display distances in results"
)
args = parser.parse_args()

query_text = " ".join(args.query)

try:
    print(f"[CHROMA] Connecting to Chroma server at http://{args.host}:{args.port}")
    client = chromadb.HttpClient(host=args.host, port=args.port)
    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=args.model
    )
    collection = client.get_or_create_collection(
        name=args.collection, embedding_function=embedding_fn
    )
except ChromaError as e:
    print(f"[ERROR] Could not connect to Chroma server: {e}")
    sys.exit(1)

print(f'[SEARCH] Searching for: "{query_text}" (top {args.count})')
results = collection.query(query_texts=[query_text], n_results=args.count)

print("\n[RESULTS]")
for i, entry in enumerate(results["documents"][0]):
    source = results["metadatas"][0][i].get("source", "unknown")
    distance_info = ""
    if args.show_distance:
        distance = results["distances"][0][i]
        distance_info = f" (distance: {distance:.4f})"
    print(f"{i + 1}. {entry.strip()[:300]}...{distance_info}")
    print(f"   └─ Source: {source}\n")
