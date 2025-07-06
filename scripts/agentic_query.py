#!/usr/bin/env python3
"""
Iterative retrieval-augmented generation using LocalAI and Qdrant.

Workflow:
1. Generate a search query from the user question (or follow-up context).
2. Embed the query via LocalAI (/v1/embeddings).
3. Search Qdrant for nearest neighbours.
4. Pass retrieval results + user question to LocalAI (/v1/chat/completions).
5. Decide whether to:
   - Issue a new search query (SEARCH_QUERY: …)
   - Or produce a final answer (FINAL_ANSWER: … [DONE])
6. Loop up to max_iterations or until FINAL_ANSWER is returned.
"""

import os
import sys
import time

import requests

# === Configuration ===
LOCALAI_URL = os.getenv("LOCALAI_URL", "http://localhost:5051")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
MODEL_NAME = os.getenv("LOCALAI_MODEL", "my_model")  # adjust to your loaded model name
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "my_collection")
RETRIEVAL_LIMIT = int(os.getenv("RETRIEVAL_LIMIT", "5"))
MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "10"))
RETRY_DELAY = float(os.getenv("RETRY_DELAY", "1.0"))  # seconds between retries

# === Helpers ===


def call_localai_chat(messages):
    """Call LocalAI chat/completions endpoint with the given messages."""
    url = f"{LOCALAI_URL}/v1/chat/completions"
    payload = {"model": MODEL_NAME, "messages": messages}
    resp = requests.post(url, json=payload)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


def embed_text(text):
    """Call LocalAI embeddings endpoint to get a vector."""
    url = f"{LOCALAI_URL}/v1/embeddings"
    payload = {"model": MODEL_NAME, "input": text}
    resp = requests.post(url, json=payload)
    resp.raise_for_status()
    # Adjust indexing if API returns differently
    return resp.json()["data"][0]["embedding"]


def search_qdrant(vector, limit=RETRIEVAL_LIMIT):
    """Search Qdrant collection for nearest neighbours."""
    url = f"{QDRANT_URL}/collections/{QDRANT_COLLECTION}/points/search"
    body = {
        "vector": vector,
        "limit": limit,
        "with_payload": True,
        "with_vector": False,
    }
    resp = requests.post(url, json=body)
    resp.raise_for_status()
    hits = resp.json().get("result", []) or resp.json().get("hits", [])
    # Extract text payload; adjust key if you store under a different field
    return [hit["payload"].get("text", "") for hit in hits]


def generate_search_query(user_query, prev_context=None):
    """Ask the LLM to generate a Qdrant search query."""
    sys_msg = {
        "role": "system",
        "content": (
            "You are a retrieval assistant. "
            "Given the user's question and any prior context, "
            "produce exactly one search query to retrieve relevant documents. "
            "Respond ONLY with: SEARCH_QUERY: <your query>"
        ),
    }
    user_msg = {
        "role": "user",
        "content": f"User question: {user_query}\n"
        f"{'Previous context: ' + prev_context if prev_context else ''}",
    }
    resp = call_localai_chat([sys_msg, user_msg])
    if not resp.startswith("SEARCH_QUERY:"):
        raise ValueError(f"Unexpected response for search query: {resp}")
    return resp.split("SEARCH_QUERY:", 1)[1].strip()


def answer_with_retrieval(user_query, retrieval_docs):
    """Ask the LLM to answer (or decide on another search) given retrievals."""
    sys_msg = {
        "role": "system",
        "content": (
            "You are a knowledgeable assistant using retrieved documents to help answer the user's question.\n"
            "If you need more information, respond with exactly: SEARCH_QUERY: <your new query>\n"
            "If you have enough to answer, respond with exactly: FINAL_ANSWER: <your answer> [DONE]\n"
            "Do not include anything else."
        ),
    }
    user_msg = {
        "role": "user",
        "content": (
            f"User question: {user_query}\n\n"
            "Retrieved documents:\n" + "\n---\n".join(retrieval_docs)
        ),
    }
    return call_localai_chat([sys_msg, user_msg])


# === Main Loop ===


def main():
    if len(sys.argv) > 1:
        user_question = " ".join(sys.argv[1:])
    else:
        user_question = input("Enter your question: ").strip()
        if not user_question:
            print("No question provided. Exiting.")
            sys.exit(1)

    prev_context = None
    for iteration in range(1, MAX_ITERATIONS + 1):
        print(f"[Iteration {iteration}] Generating search query…")
        try:
            query = generate_search_query(user_question, prev_context)
        except Exception as e:
            print(f"Error generating search query: {e}")
            break

        print(f"[Iteration {iteration}] Embedding & searching Qdrant for: “{query}”")
        try:
            vec = embed_text(query)
            docs = search_qdrant(vec)
        except Exception as e:
            print(f"Error during retrieval: {e}")
            break

        print(
            f"[Iteration {iteration}] Retrieved {len(docs)} documents. Asking LLM for next step…"
        )
        try:
            response = answer_with_retrieval(user_question, docs)
        except Exception as e:
            print(f"Error calling completion endpoint: {e}")
            break

        if response.startswith("SEARCH_QUERY:"):
            prev_context = f"Previously searched: {query}\nRetrieved docs: {docs}"
            # Sleep briefly to avoid rate limits
            time.sleep(RETRY_DELAY)
            continue

        if response.startswith("FINAL_ANSWER:"):
            final = response.split("FINAL_ANSWER:", 1)[1].rstrip("[DONE]").strip()
            print("\n=== Final Answer ===")
            print(final)
            return

        # Fallback: treat entire response as final
        print("\n=== Answer ===")
        print(response)
        return

    print("\nReached maximum iterations without a final answer.")


if __name__ == "__main__":
    main()
