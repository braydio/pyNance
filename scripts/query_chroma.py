# scripts/query_chroma.py

import argparse
import chromadb
import sys
import os
from chromadb.errors import ChromaError

DEFAULT_COLLECTION = os.getenv("CHROMA_COLLECTION", "pynance-code")
DEFAULT_COUNT = int(os.getenv("CHROMA_RESULT_COUNT", 3))
DEFAULT_HOST = os.getenv("CHROMA_HOST", "localhost")
DEFAULT_PORT = int(os.getenv("CHROMA_PORT", 8055))

parser = argparse.ArgumentParser(description="Query ChromaDB for similar documents.")
parser.add_argument("query", nargs="+", help="Query text")
parser.add_argument(
    "-n", "--count", type=int, default=DEFAULT_COUNT, help="Number of results to return"
)
parser.add_argument("--collection", default=DEFAULT_COLLECTION, help="Collection name")
parser.add_argument("--host", default=DEFAULT_HOST, help="ChromaDB host")
parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="ChromaDB port")
args = parser.parse_args()

query_text = " ".join(args.query)

try:
    print(f"[CHROMA] Connecting to Chroma server at http://{args.host}:{args.port}")
    client = chromadb.HttpClient(host=args.host, port=args.port)
    collection = client.get_or_create_collection(name=args.collection)
except ChromaError as e:
    print(f"[ERROR] Could not connect to Chroma server: {e}")
    sys.exit(1)

print(f'[SEARCH] Searching for: "{query_text}" (top {args.count})')
results = collection.query(query_texts=[query_text], n_results=args.count)

print("\n[RESULTS]")
for i, entry in enumerate(results["documents"][0]):
    source = results["metadatas"][0][i].get("source", "unknown")
    print(f"{i + 1}. {entry.strip()[:300]}...")  # preview first 300 chars
    print(f"   └─ Source: {source}\n")
