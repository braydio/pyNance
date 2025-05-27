# query_chroma.py
import sys
import chromadb
from chromadb.config import Settings

COLLECTION_NAME = "pynance-code"
COUNT = 3

if len(sys.argv) < 2:
    print('Usage: python scripts/query_chroma.py "query text ..."')
    sys.exit(1)

query_text = " ".join(sys.argv[1:])

client = chromadb.Client(
    Settings(persist_directory=".chroma_store", anonymized_telemetry=False)
)

collection = client.get_or_create_collection(name=COLLECTION_NAME)


print(f'[SEARCH] Finding results for "{query_text}" ...')
results = collection.query(query_texts=[query_text], n_results=COUNT)

for i, entry in enumerate(results["documents"][0]):
    print(f"\n| {i + 1}. ... ")
    print(entry)
    print(" -- Source: " + results["metadatas"][0][i]["source"])
