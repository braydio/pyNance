"""Integration test for ``scripts/query_chroma.py``.

This test runs the script against a temporary Chroma collection using a
lightweight embedding function to avoid heavy downloads.
"""

import runpy
import sys
from pathlib import Path

import chromadb
import pytest
from chromadb.utils import embedding_functions


class DummyEmbeddingFunction:
    """Simple embedding function for deterministic results."""

    def __call__(self, input):
        if isinstance(input, str):
            input = [input]
        return [[float(len(s)), 0.0, 0.0] for s in input]

    def name(self):
        return "dummy"

    def embed_documents(self, documents):
        return self(documents)

    def embed_query(self, text):
        return self([text])[0]

    def is_legacy(self):
        """Indicate legacy embedding function to suppress deprecation warnings."""
        return True


@pytest.fixture()
def local_chroma(tmp_path):
    """Create a temporary Chroma collection with sample documents."""
    client = chromadb.PersistentClient(path=str(tmp_path))
    ef = DummyEmbeddingFunction()
    collection = client.get_or_create_collection("test", embedding_function=ef)
    collection.add(
        ids=["1", "2"],
        documents=["hello world", "goodbye world"],
        metadatas=[{"source": "s1"}, {"source": "s2"}],
    )
    return collection


class LocalHttpClient:
    """Mimic ``chromadb.HttpClient`` for local testing."""

    def __init__(self, *_, **__):
        self.collection = None

    def get_or_create_collection(self, name, **_):
        return self.collection


def test_query_chroma_outputs_results(monkeypatch, capsys, local_chroma):
    """Verify query_chroma prints documents from the local collection."""
    client_stub = LocalHttpClient()
    client_stub.collection = local_chroma
    monkeypatch.setattr("chromadb.HttpClient", lambda *a, **k: client_stub)
    monkeypatch.setattr(
        embedding_functions,
        "SentenceTransformerEmbeddingFunction",
        lambda *a, **k: DummyEmbeddingFunction(),
    )

    orig_argv = sys.argv
    sys.argv = ["query_chroma.py", "hello", "-n", "1", "--collection", "test"]
    try:
        runpy.run_path(Path("scripts") / "query_chroma.py", run_name="__main__")
    finally:
        sys.argv = orig_argv

    output = capsys.readouterr().out
    assert "[RESULTS]" in output
    assert "hello world" in output
