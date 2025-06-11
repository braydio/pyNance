#!/usr/bin/env python3

"""
Iterative RAG using TextGen Web UI and Qdrant.
"""

import os
import sys
import requests
import json
import time

# === Config ===
TGI_URL = os.getenv("TEXTGEN_URL", "http://localhost:5051")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "my_collection")
RETRIEVAL_LIMIT = int(os.getenv("RETRIEVAL_LIMIT", "5"))
MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "10"))
RETRY_DELAY = float(os.getenv("RETRY_DELAY", "1.0"))

# === Helpers ===


def call_textgen(prompt):
    """Call textgen-webui /api/v1/completions endpoint."""
    url = f"{TGI_URL}/api/v1/completions"
    payload = {
        "prompt": prompt,
        "max_new_tokens": 256,
        "temperature": 0.7,
        "stop": ["[DONE]"],
    }
    r = requests.post(url, json=payload)
    r.raise_for_status()
    return r.json()["results"][0]["text"].strip()


def embed_text(text):
    """Use a local sentence-transformers model or external embedding API."""
    # You can replace this with a call to your own model/server.
    import sentence_transformers

    model = sentence_transformers.SentenceTransformer("all-MiniLM-L6-v2")
    return model.encode(text).tolist()


def search_qdrant(vector, limit=RETRIEVAL_LIMIT):
    url = f"{QDRANT_URL}/collections/{QDRANT_COLLECTION}/points/search"
    body = {
        "vector": vector,
        "limit": limit,
        "with_payload": True,
        "with_vector": False,
    }
    r = requests.post(url, json=body)
    r.raise_for_status()
    results = r.json().get("result", []) or r.json().get("hits", [])
    return [r["payload"].get("text", "") for r in results]


def generate_search_query(user_query, prev_context=None):
    prompt = (
        "You are a retrieval assistant.\n"
        f"User question: {user_query}\n"
        f"{'Previous context: ' + prev_context if prev_context else ''}\n"
        "Respond only as: SEARCH_QUERY: <query>"
    )
    response = call_textgen(prompt)
    if not response.startswith("SEARCH_QUERY:"):
        raise ValueError("Unexpected response: " + response)
    return response.split("SEARCH_QUERY:", 1)[1].strip()


def answer_with_retrieval(user_query, retrieved_docs):
    joined_docs = "\n---\n".join(retrieved_docs)
    prompt = (
        "You are a helpful assistant using retrieved documents.\n"
        "Respond with:\n"
        "- SEARCH_QUERY: <text> if more info is needed\n"
        "- FINAL_ANSWER: <answer> [DONE] if ready to answer\n\n"
        f"User question: {user_query}\n\nRetrieved documents:\n{joined_docs}"
    )
    return call_textgen(prompt)


# === Main Loop ===


def main():
    if len(sys.argv) > 1:
        user_question = " ".join(sys.argv[1:])
    else:
        user_question = input("Enter your question: ").strip()
        if not user_question:
            print("No question given. Exiting.")
            return

    prev_context = None
    for i in range(1, MAX_ITERATIONS + 1):
        print(f"[{i}] Generating search query...")
        try:
            query = generate_search_query(user_question, prev_context)
        except Exception as e:
            print("Failed to generate query:", e)
            break

        print(f"[{i}] Embedding and retrieving for query: {query}")
        try:
            vector = embed_text(query)
            docs = search_qdrant(vector)
        except Exception as e:
            print("Retrieval failed:", e)
            break

        print(f"[{i}] Retrieved {len(docs)} docs. Asking LLM...")
        try:
            response = answer_with_retrieval(user_question, docs)
        except Exception as e:
            print("Completion error:", e)
            break

        if response.startswith("SEARCH_QUERY:"):
            prev_context = f"Query: {query}\nDocs: {docs}"
            time.sleep(RETRY_DELAY)
            continue

        if response.startswith("FINAL_ANSWER:"):
            answer = response.split("FINAL_ANSWER:", 1)[1].rstrip("[DONE]").strip()
            print("\n=== Final Answer ===\n" + answer)
            return

        # fallback
        print("\n=== Answer ===\n" + response)
        return

    print("Max iterations reached without answer.")


if __name__ == "__main__":
    main()
