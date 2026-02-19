"""Golden set evaluation for knowledge retrieval quality.

This test file defines a golden set of 25 test queries with expected
topics/sources, and evaluates recall@5 against the knowledge base.

These tests are marked as integration tests and require an initialized
knowledge base to run. Skip with: pytest -m "not integration"
"""

import pytest

# Integration tests require an initialized knowledge base
# Run with: pytest -m integration


# =============================================================================
# Golden Set Definition
# =============================================================================

GOLDEN_SET = [
    {
        "query": "How do I create a server group?",
        "expected_topics": ["server group", "creating"],
        "expected_sources": ["user guide", "admin guide"],
    },
    {
        "query": "What is a compound service?",
        "expected_topics": ["compound service"],
        "expected_sources": ["user guide"],
    },
    {
        "query": "How to set up monitoring for a new server?",
        "expected_topics": ["server", "monitoring", "setup"],
        "expected_sources": ["user guide"],
    },
    {
        "query": "What network services can FortiMonitor check?",
        "expected_topics": ["network service"],
        "expected_sources": ["user guide", "admin guide"],
    },
    {
        "query": "How do I configure notification schedules?",
        "expected_topics": ["notification", "schedule"],
        "expected_sources": ["user guide", "admin guide"],
    },
    {
        "query": "What is a maintenance window and how do I create one?",
        "expected_topics": ["maintenance"],
        "expected_sources": ["user guide"],
    },
    {
        "query": "How to acknowledge an outage?",
        "expected_topics": ["outage", "acknowledge"],
        "expected_sources": ["user guide"],
    },
    {
        "query": "What agent resources are available?",
        "expected_topics": ["agent resource"],
        "expected_sources": ["user guide", "admin guide"],
    },
    {
        "query": "How to configure SNMP monitoring?",
        "expected_topics": ["snmp"],
        "expected_sources": ["user guide", "admin guide"],
    },
    {
        "query": "What are server templates used for?",
        "expected_topics": ["template"],
        "expected_sources": ["user guide"],
    },
    {
        "query": "How to set up contact groups for alerting?",
        "expected_topics": ["contact group", "alert"],
        "expected_sources": ["user guide", "admin guide"],
    },
    {
        "query": "What is the FortiMonitor API base URL?",
        "expected_topics": ["api"],
        "expected_sources": ["admin guide", "user guide"],
    },
    {
        "query": "How do I create a dashboard?",
        "expected_topics": ["dashboard"],
        "expected_sources": ["user guide"],
    },
    {
        "query": "What cloud providers does FortiMonitor support?",
        "expected_topics": ["cloud"],
        "expected_sources": ["user guide", "admin guide"],
    },
    {
        "query": "How to configure a status page?",
        "expected_topics": ["status page"],
        "expected_sources": ["user guide"],
    },
    {
        "query": "What is DEM and how does it work?",
        "expected_topics": ["dem", "digital experience"],
        "expected_sources": ["user guide"],
    },
    {
        "query": "How do I troubleshoot server connectivity issues?",
        "expected_topics": ["troubleshoot", "connectivity"],
        "expected_sources": ["user guide", "admin guide"],
    },
    {
        "query": "What metrics can I monitor on a server?",
        "expected_topics": ["metric"],
        "expected_sources": ["user guide"],
    },
    {
        "query": "How to set up rotating contacts?",
        "expected_topics": ["rotating contact"],
        "expected_sources": ["user guide", "admin guide"],
    },
    {
        "query": "What is a monitoring node?",
        "expected_topics": ["monitoring node"],
        "expected_sources": ["user guide", "admin guide"],
    },
    {
        "query": "How to export outage history?",
        "expected_topics": ["outage", "export", "history"],
        "expected_sources": ["user guide"],
    },
    {
        "query": "What are countermeasures in FortiMonitor?",
        "expected_topics": ["countermeasure"],
        "expected_sources": ["user guide", "admin guide"],
    },
    {
        "query": "How do I manage user permissions?",
        "expected_topics": ["user", "permission"],
        "expected_sources": ["admin guide"],
    },
    {
        "query": "What Fabric integration features are available?",
        "expected_topics": ["fabric"],
        "expected_sources": ["user guide", "admin guide"],
    },
    {
        "query": "How to view server availability reports?",
        "expected_topics": ["availability", "report"],
        "expected_sources": ["user guide"],
    },
]


# =============================================================================
# Evaluation Helpers
# =============================================================================


def _topic_match(result_text: str, expected_topics: list[str]) -> bool:
    """Check if any expected topic appears in the result text."""
    text_lower = result_text.lower()
    return any(topic.lower() in text_lower for topic in expected_topics)


def _source_match(source_name: str, expected_sources: list[str]) -> bool:
    """Check if the result source matches any expected source."""
    source_lower = source_name.lower()
    return any(expected.lower() in source_lower for expected in expected_sources)


# =============================================================================
# Integration Tests
# =============================================================================


@pytest.mark.integration
class TestRetrievalQuality:
    """Evaluate retrieval quality using the golden set.

    These tests require an initialized knowledge base and are marked
    as integration tests. Run with: pytest -m integration
    """

    @pytest.fixture
    def knowledge_store(self):
        """Get the knowledge base vector store."""
        import os
        from src.knowledge.store.vector_store import VectorStore

        db_path = os.environ.get("KNOWLEDGE_BASE_PATH", "data/vectordb")
        store = VectorStore(db_path=db_path)

        # Skip if store is empty
        status = store.get_status()
        if status.total_chunks == 0:
            pytest.skip("Knowledge base is empty — run ingestion first")

        return store

    @pytest.fixture
    def embedder(self):
        """Get the embedder for query embedding."""
        import os
        from src.knowledge.ingestion.embedder import Embedder

        model = os.environ.get("KNOWLEDGE_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        return Embedder(model_name=model)

    def test_recall_at_5(self, knowledge_store, embedder):
        """Evaluate recall@5: at least 80% of golden set queries should
        return a relevant result in the top 5.
        """
        hits = 0
        misses = []

        for item in GOLDEN_SET:
            query = item["query"]
            query_embedding = embedder.embed_query(query)
            results = knowledge_store.search(
                query_embedding=query_embedding, top_k=5
            )

            # Check if any result matches expected topics or sources
            found = False
            for result in results:
                if _topic_match(result.text, item["expected_topics"]):
                    found = True
                    break
                if _source_match(
                    result.metadata.source_name, item["expected_sources"]
                ):
                    found = True
                    break

            if found:
                hits += 1
            else:
                misses.append(query)

        recall = hits / len(GOLDEN_SET)

        if misses:
            miss_list = "\n  - ".join(misses)
            print(f"\nMissed queries ({len(misses)}):\n  - {miss_list}")

        assert recall >= 0.80, (
            f"Recall@5 = {recall:.2%} ({hits}/{len(GOLDEN_SET)}), "
            f"expected >= 80%. Missed: {misses}"
        )

    def test_all_queries_return_results(self, knowledge_store, embedder):
        """Verify that every golden set query returns at least 1 result."""
        no_results = []

        for item in GOLDEN_SET:
            query_embedding = embedder.embed_query(item["query"])
            results = knowledge_store.search(
                query_embedding=query_embedding, top_k=5
            )
            if len(results) == 0:
                no_results.append(item["query"])

        assert len(no_results) == 0, (
            f"{len(no_results)} queries returned no results: {no_results}"
        )

    def test_result_scores_reasonable(self, knowledge_store, embedder):
        """Verify that top results have reasonable similarity scores."""
        low_score_queries = []

        for item in GOLDEN_SET:
            query_embedding = embedder.embed_query(item["query"])
            results = knowledge_store.search(
                query_embedding=query_embedding, top_k=1
            )
            if results and results[0].score < 0.3:
                low_score_queries.append(
                    (item["query"], results[0].score)
                )

        if low_score_queries:
            details = "\n  ".join(
                f"'{q}': score={s:.3f}" for q, s in low_score_queries
            )
            print(f"\nLow-score queries:\n  {details}")

        # Allow up to 20% of queries to have low scores
        max_low = int(len(GOLDEN_SET) * 0.2)
        assert len(low_score_queries) <= max_low, (
            f"{len(low_score_queries)} queries had low top-1 scores "
            f"(max allowed: {max_low})"
        )


# =============================================================================
# Unit Test: Golden Set Completeness
# =============================================================================


class TestGoldenSetCompleteness:
    """Verify the golden set itself is well-formed."""

    def test_golden_set_has_enough_queries(self):
        assert len(GOLDEN_SET) >= 20, (
            f"Golden set has {len(GOLDEN_SET)} queries, need at least 20"
        )

    def test_golden_set_queries_are_unique(self):
        queries = [item["query"] for item in GOLDEN_SET]
        assert len(queries) == len(set(queries)), "Duplicate queries in golden set"

    def test_golden_set_has_expected_fields(self):
        for item in GOLDEN_SET:
            assert "query" in item, f"Missing 'query' field: {item}"
            assert "expected_topics" in item, f"Missing 'expected_topics': {item}"
            assert "expected_sources" in item, f"Missing 'expected_sources': {item}"
            assert len(item["expected_topics"]) > 0
            assert len(item["expected_sources"]) > 0

    def test_golden_set_covers_diverse_topics(self):
        all_topics = set()
        for item in GOLDEN_SET:
            for topic in item["expected_topics"]:
                all_topics.add(topic.lower())

        # Should cover at least 10 distinct topic areas
        assert len(all_topics) >= 10, (
            f"Golden set covers only {len(all_topics)} topics, need at least 10"
        )
