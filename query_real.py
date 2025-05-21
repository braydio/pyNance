import sys
import chromadb
from chromadb.config import Settings
import textwrap

query = sys.argv[1] if len(sys.argv) > 1 else "How does pyNance forecast?"

client = chromadb.Client(
    Settings(
        chroma_api_impl="rest",
        chroma_server_host="localhost",
        chroma_server_http_port=8055,
    )
)

collection = client.get_collection("pynance-code")
results = collection.query(query_texts=[query], n_results=3)

for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
    print(f"\n📄 From: {meta['source']}\n{textwrap.fill(doc, width=100)}\n")
