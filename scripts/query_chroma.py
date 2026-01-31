"""Interactive QA over a Chroma collection."""

import argparse
import os
import sys
import textwrap

import chromadb
import requests
from chromadb.errors import ChromaError
from chromadb.utils import embedding_functions

DEFAULT_COLLECTION = os.getenv("CHROMA_COLLECTION", "pynance-code")
DEFAULT_COUNT = int(os.getenv("CHROMA_RESULT_COUNT", 3))
DEFAULT_HOST = os.getenv("CHROMA_HOST", "localhost")
DEFAULT_PORT = int(os.getenv("CHROMA_PORT", 8055))
DEFAULT_MODEL = os.getenv("CHROMA_MODEL", "all-MiniLM-L6-v2")
DEFAULT_TENANT = os.getenv("CHROMA_TENANT")
DEFAULT_DATABASE = os.getenv("CHROMA_DATABASE")
DEFAULT_LLM_URL = os.getenv("OLLAMA_GENERATE_URL")
DEFAULT_LLM_MODEL = os.getenv("OLLAMA_LLM_MODEL")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Query ChromaDB for similar documents."
    )
    parser.add_argument("-q", "--query", help="Run a single query and exit.")
    parser.add_argument("-n", "--count", type=int, default=DEFAULT_COUNT)
    parser.add_argument("--collection", default=DEFAULT_COLLECTION)
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--tenant", default=DEFAULT_TENANT)
    parser.add_argument("--database", default=DEFAULT_DATABASE)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--show-distance", action="store_true")
    parser.add_argument("--show-results", action="store_true")
    parser.add_argument("--llm-url", default=DEFAULT_LLM_URL)
    parser.add_argument("--llm-model", default=DEFAULT_LLM_MODEL)
    parser.add_argument("--no-llm", action="store_true")
    return parser.parse_args()


def build_client(args):
    client_kwargs = {"host": args.host, "port": args.port}
    if args.tenant:
        client_kwargs["tenant"] = args.tenant
    if args.database:
        client_kwargs["database"] = args.database
    return chromadb.HttpClient(**client_kwargs)


def build_collection(client, args):
    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=args.model
    )
    return client.get_or_create_collection(
        name=args.collection, embedding_function=embedding_fn
    )


def query_collection(collection, question, count):
    results = collection.query(query_texts=[question], n_results=count)
    documents = results.get("documents", [[]])[0] or []
    metadatas = results.get("metadatas", [[]])[0] or []
    distances = results.get("distances", [[]])[0] or []
    return documents, metadatas, distances


def format_results(documents, metadatas, distances, show_distance):
    lines = ["[RESULTS]"]
    for i, doc in enumerate(documents):
        meta = metadatas[i] if i < len(metadatas) else {}
        source = meta.get("source") or meta.get("relative_path", "unknown")
        tags = meta.get("tags", "")
        summary = meta.get("docstrings", "")
        distance_info = ""
        if show_distance and i < len(distances):
            distance_info = f" (distance: {distances[i]:.4f})"

        snippet = doc.strip().replace("\n", " ")
        lines.append(f"{i + 1}. {snippet[:300]}...{distance_info}")
        lines.append(f"   - Source: {source}")
        if tags:
            lines.append(f"   - Tags: {tags}")
        if summary:
            lines.append(f"   - Summary: {summary[:150]}")
        lines.append("")
    return "\n".join(lines)


def build_prompt(question, options_text, documents, metadatas):
    context_block = "\n\n".join(
        f"[{meta.get('relative_path', meta.get('source', 'unknown'))} | "
        f"chunk {meta.get('chunk_index', 'n/a')}]\n{doc}"
        for doc, meta in zip(documents, metadatas)
    )

    options_block = ""
    if options_text:
        options_block = f"\nOptions:\n{options_text.strip()}\n"

    rules = [
        "- Use ONLY the provided context",
        "- Do NOT add external knowledge",
        "- If the answer is not present, say so clearly",
    ]
    if options_text:
        rules.append(
            "- If options are provided, choose the single best option and respond "
            "with its letter and a one-sentence justification"
        )

    prompt = f"""
You are an expert assistant for the pyNance codebase.

RULES:
{chr(10).join(rules)}

Context:
{context_block}

Question:
{question}{options_block}

Answer clearly and concisely.
""".strip()
    return prompt


def generate_answer(llm_url, llm_model, prompt):
    resp = requests.post(
        llm_url,
        json={
            "model": llm_model,
            "prompt": prompt,
            "stream": False,
        },
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()
    if "response" in data and data["response"]:
        return data["response"].strip()
    if "error" in data and data["error"]:
        raise RuntimeError(f"LLM generate error: {data['error']}")
    raise KeyError(f"Missing 'response' in LLM output: {data}")


def prompt_question():
    return input("\nQuestion (or 'exit'): ").strip()


def prompt_options():
    print("Options (one per line, blank line to finish). Press enter to skip:")
    lines = []
    while True:
        line = input().rstrip()
        if not line:
            break
        lines.append(line)
    return "\n".join(lines) if lines else None


def handle_question(args, collection, question, options_text):
    documents, metadatas, distances = query_collection(collection, question, args.count)
    if not documents:
        print("No relevant context found.")
        return

    use_llm = not args.no_llm and args.llm_url and args.llm_model
    if use_llm:
        prompt = build_prompt(question, options_text, documents, metadatas)
        try:
            answer = generate_answer(args.llm_url, args.llm_model, prompt)
            print("\nAnswer:\n")
            print(textwrap.fill(answer, 100))
        except requests.RequestException as exc:
            print(f"[ERROR] LLM request failed: {exc}")
    else:
        if not args.no_llm and (args.llm_url or args.llm_model):
            print("[INFO] LLM not fully configured; showing matching context.")
        print(format_results(documents, metadatas, distances, args.show_distance))

    if args.show_results and use_llm:
        print(format_results(documents, metadatas, distances, args.show_distance))


def main():
    args = parse_args()
    try:
        client = build_client(args)
        collection = build_collection(client, args)
    except ChromaError as exc:
        print(f"[ERROR] Failed to connect to ChromaDB: {exc}")
        sys.exit(1)

    can_use_llm = not args.no_llm and args.llm_url and args.llm_model
    if args.query:
        handle_question(args, collection, args.query, options_text=None)
        return

    while True:
        question = prompt_question()
        if question.lower() in {"exit", "quit"}:
            break
        if not question:
            continue
        options_text = prompt_options() if can_use_llm else None
        handle_question(args, collection, question, options_text)


if __name__ == "__main__":
    main()
