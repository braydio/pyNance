# --- launch_qdrant_local.py ---
# Launch Qdrant in-process without Docker (for local testing)

from qdrant_client.local import QdrantLocal

if __name__ == "__main__":
    print("[QDRANT] Starting embedded Qdrant server...")
    qdrant = QdrantLocal(path="./qdrant_embedded")
    qdrant.run()
    print("[QDRANT] Running on http://localhost:6333")
