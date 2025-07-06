import os

import chromadb
from chromadb.config import Settings

# Constants
SOURCE_DIR = "/home/braydenchaffee/Projects/pyNance/backend"
CHROMA_HOST = "localhost"
CHROMA_PORT = 8055
COLLECTION_NAME = "pynance-code"

# Connect to ChromaDB
client = chromadb.Client(
    Settings(
        chroma_api_impl="rest",
        chroma_server_host=CHROMA_HOST,
        chroma_server_http_port=CHROMA_PORT,
    )
)

# Create or get existing collection
collection = client.get_or_create_collection(name=COLLECTION_NAME)


# Helper function to chunk text
def chunk_text(text, max_length=1000):
    return [text[i : i + max_length] for i in range(0, len(text), max_length)]


# Add .py files to the collection
doc_count = 0
for root, _, files in os.walk(SOURCE_DIR):
    for filename in files:
        if filename.endswith(".py"):
            path = os.path.join(root, filename)
            with open(path, "r", encoding="utf-8") as file:
                content = file.read()
                chunks = chunk_text(content)
                for i, chunk in enumerate(chunks):
                    doc_id = f"{filename}-{i}"
                    collection.add(
                        documents=[chunk], metadatas=[{"source": path}], ids=[doc_id]
                    )
                    doc_count += 1

print(f"Indexed {doc_count} code chunks into ChromaDB collection '{COLLECTION_NAME}'.")
