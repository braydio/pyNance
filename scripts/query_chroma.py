# scripts/query_chroma.py

import argparse
import chromadb
import sys
import os
import json
from chromadb.errors import ChromaError

# Defaults
DEFAULT_COLLECTION = os.getenv("CHROMA_COLLECTION", "pynance-code")
DEFAULT_COUNT = int(os.getenv("CHROMA_RESULT_COUNT", 3))
DEFAULT_HOST = os.getenv("CHROMA_HOST", "localhost")
DEFAULT_PORT = int(os.getenv("CHROMA_PORT", 8055))

# CLI Argument Parser
parser = argparse.ArgumentParser(
    description="Query ChromaDB for similar documents.",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)
parser.add_argument("query", nargs="+", help="Query text")
parser.add_argument(
    "-n", "--count", type=int, default=DEFAULT_COUNT, help="Number of results to return"
)
parser.add_argument("--collection", default=DEFAULT_COLLECTION, help="Collection name")
parser.add_argument("--host", default=DEFAULT_HOST, help="ChromaDB host")
parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="ChromaDB port")
parser.add_argument("--json", action="store_true", help="Output results as JSON")
args = parser.parse_args()

query_text = " ".join(args.query)

# Connect to Chroma
try:
    client = chromadb.HttpClient(host=args.host, port=args.port)
    collection = client.get_or_create_collection(name=args.collection)
except ChromaError as e:
    print(f"[ERROR] Could not connect to Chroma server: {e}")
    sys.exit(1)

# Execute query
results = collection.query(query_texts=[query_text], n_results=args.count)
documents = results["documents"][0]
metadatas = results["metadatas"][0]

# Output results
if args.json:
    output = [
        {
            "rank": i + 1,
            "document": doc,
            "source": metadatas[i].get("source", "unknown"),
        }
        for i, doc in enumerate(documents)
    ]
    print(json.dumps(output, indent=2))
else:
    print(f'\n[SEARCH] Query: "{query_text}" (Top {args.count})\n')
    for i, entry in enumerate(documents):
        source = metadatas[i].get("source", "unknown")
        preview = entry.strip().replace("\n", " ")[:300]
        print(f"{i + 1}. {preview}...")
        print(f"   └─ Source: {source}\n")
