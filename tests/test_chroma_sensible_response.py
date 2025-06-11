# test/test_chroma_sensible_response.py
import pytest
import chromadb
import logging

logger = logging.getLogger("test_chroma")
logging.basicConfig(level=logging.INFO)


@pytest.mark.integration
def test_chroma_query_with_logging():
    try:
        client = chromadb.HttpClient(host="localhost", port=8055)
        collection = client.get_or_create_collection(name="pynance-code")

        total_docs = collection.count()
        logger.info(f"[CHROMA] Collection 'pynance-code' has {total_docs} documents")

        if total_docs == 0:
            pytest.skip("Chroma collection is empty — nothing to query")

        query_text = "how do I save a recurring transaction?"
        logger.info(f'[CHROMA] Querying: "{query_text}"')
        response = collection.query(query_texts=[query_text], n_results=3)

        docs = response.get("documents", [[]])[0]
        metas = response.get("metadatas", [[]])[0]

        assert docs, "No documents returned from Chroma"

        # Log response summary
        for i, (doc, meta) in enumerate(zip(docs, metas)):
            snippet = doc[:120].replace("\n", " ").strip()
            logger.info(f"[MATCH {i + 1}] {snippet}")
            logger.info(f"  └─ Metadata: {meta}")

        # Loosely verify relevance
        full_text = " ".join(docs).lower()
        assert any(
            word in full_text for word in ["recurring", "transaction", "frequency"]
        ), "Response doesn't contain expected semantic terms"

    except Exception as e:
        pytest.fail(f"Chroma query failed: {e}")
