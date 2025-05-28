# query_chroma.py
import sys
import chromadb

COLLECTION_NAME = "pynance-code"
COUNT = 3

if len(sys.argv) < 2:
    print('Usage: python scripts/query_chroma.py "query text ..."')
    sys.exit(1)

query_text = " ".join(sys.argv[1:])

print("[CHROMA] Connecting to Chroma server at http://localhost:8000")
client = chromadb.HttpClient(host="localhost", port=8000)

collection = client.get_or_create_collection(name=COLLECTION_NAME)

print(f'[SEARCH] Finding results for "{query_text}" ...')
results = collection.query(query_texts=[query_text], n_results=COUNT)

for i, entry in enumerate(results["documents"][0]):
    print(f"\n| {i + 1}. ... ")
    print(entry)
    print(" -- Source: " + results["metadatas"][0][i]["source"])
