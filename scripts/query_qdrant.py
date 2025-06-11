# --- query_qdrant.py ---

import argparse
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

parser = argparse.ArgumentParser(description="Query Qdrant for similar documents")
parser.add_argument("query", nargs="+", help="Query text")
parser.add_argument("--count", type=int, default=3, help="Results to return")
args = parser.parse_args()

query_text = " ".join(args.query)
encoder = SentenceTransformer("all-MiniLM-L6-v2")
vector = encoder.encode(query_text)

client = QdrantClient("localhost", port=6333)
results = client.search(
    collection_name="pynance-code", query_vector=vector, limit=args.count
)

print("\n[QDRANT] Search Results:\n")
for i, r in enumerate(results, 1):
    preview = r.payload.get("docstring_summary") or str(r.payload)[:200]
    print(f"{i}. Score: {r.score:.3f}  →  {preview}")
    print(f"   └ Source: {r.payload.get('source', 'unknown')}\n")

# --- launch_qdrant_local.py ---
# Launch Qdrant in-process without Docker (for local testing)

from qdrant_client.local import QdrantLocal

if __name__ == "__main__":
    print("[QDRANT] Starting embedded Qdrant server...")
    qdrant = QdrantLocal(path="./qdrant_embedded")
    qdrant.run()
    print("[QDRANT] Running on http://localhost:6333")
