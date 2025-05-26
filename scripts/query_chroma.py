# query_chroma.py
import sys
import chromadb
from chromadb.config import Settings

COLLECTION_NAME = "pynance-code"
COUNT = 3
if len(sys.argv) < 1:
    print("Usage: python scripts/query_chroma.py \"query text ...\"")
    sys.exit(1)

query_text = ' '.join(sys.argv[1:])

client = chromadb.Client(Settings(
    chroma_api_imp="rest",
    chroma_server_host="localhost",
    chroma_server_http_port=8055,
)

collection = client.get_collection(name=COLLECTION_NAME)

print(f"[SECARCH] Finding results for "${query_text}" ...")
results = collection.query(query_texts=[query_text], n_results=COUNT)

for i, entry in enumerate(results["results"][0]):
    print(f"\n| {i+1}. ... ")
    print(entry)
    print(" -- Source: " + results["metadatas"][0][i]["source"])
