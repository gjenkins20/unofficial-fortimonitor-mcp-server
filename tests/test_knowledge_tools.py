"""Tests for Knowledge Layer MCP tools.

Tests search, retrieval, and management tool definitions and handlers
using mock vector store and embedder instances.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from mcp.types import TextContent


# =============================================================================
# Search Tool Tests
# =============================================================================


class TestSearchToolDefinitions:
    """Test search tool definitions have required fields."""

    def test_search_documentation_definition(self):
        from src.knowledge.tools.search import search_documentation_tool_definition

        tool = search_documentation_tool_definition()
        assert tool.name == "search_documentation"
        assert tool.description
        assert "query" in tool.inputSchema["properties"]
        assert "query" in tool.inputSchema["required"]

    def test_search_api_docs_definition(self):
        from src.knowledge.tools.search import search_api_docs_tool_definition

        tool = search_api_docs_tool_definition()
        assert tool.name == "search_api_docs"
        assert tool.description
        assert "query" in tool.inputSchema["properties"]
        assert "query" in tool.inputSchema["required"]

    def test_search_troubleshooting_definition(self):
        from src.knowledge.tools.search import search_troubleshooting_tool_definition

        tool = search_troubleshooting_tool_definition()
        assert tool.name == "search_troubleshooting"
        assert tool.description
        assert "query" in tool.inputSchema["properties"]
        assert "query" in tool.inputSchema["required"]

    def test_search_definitions_dict_completeness(self):
        from src.knowledge.tools.search import (
            KNOWLEDGE_SEARCH_TOOL_DEFINITIONS,
            KNOWLEDGE_SEARCH_HANDLERS,
        )

        assert set(KNOWLEDGE_SEARCH_TOOL_DEFINITIONS.keys()) == set(
            KNOWLEDGE_SEARCH_HANDLERS.keys()
        )
        assert len(KNOWLEDGE_SEARCH_TOOL_DEFINITIONS) == 3


# =============================================================================
# Retrieval Tool Tests
# =============================================================================


class TestRetrievalToolDefinitions:
    """Test retrieval tool definitions have required fields."""

    def test_get_doc_section_definition(self):
        from src.knowledge.tools.retrieval import get_doc_section_tool_definition

        tool = get_doc_section_tool_definition()
        assert tool.name == "get_doc_section"
        assert tool.description
        assert "section_heading" in tool.inputSchema["properties"]
        assert "section_heading" in tool.inputSchema["required"]

    def test_list_doc_topics_definition(self):
        from src.knowledge.tools.retrieval import list_doc_topics_tool_definition

        tool = list_doc_topics_tool_definition()
        assert tool.name == "list_doc_topics"
        assert tool.description

    def test_get_release_notes_definition(self):
        from src.knowledge.tools.retrieval import get_release_notes_tool_definition

        tool = get_release_notes_tool_definition()
        assert tool.name == "get_release_notes"
        assert tool.description

    def test_retrieval_definitions_dict_completeness(self):
        from src.knowledge.tools.retrieval import (
            KNOWLEDGE_RETRIEVAL_TOOL_DEFINITIONS,
            KNOWLEDGE_RETRIEVAL_HANDLERS,
        )

        assert set(KNOWLEDGE_RETRIEVAL_TOOL_DEFINITIONS.keys()) == set(
            KNOWLEDGE_RETRIEVAL_HANDLERS.keys()
        )
        assert len(KNOWLEDGE_RETRIEVAL_TOOL_DEFINITIONS) == 3


# =============================================================================
# Management Tool Tests
# =============================================================================


class TestManagementToolDefinitions:
    """Test management tool definitions have required fields."""

    def test_refresh_knowledge_base_definition(self):
        from src.knowledge.tools.management import (
            refresh_knowledge_base_tool_definition,
        )

        tool = refresh_knowledge_base_tool_definition()
        assert tool.name == "refresh_knowledge_base"
        assert tool.description

    def test_get_knowledge_base_status_definition(self):
        from src.knowledge.tools.management import (
            get_knowledge_base_status_tool_definition,
        )

        tool = get_knowledge_base_status_tool_definition()
        assert tool.name == "get_knowledge_base_status"
        assert tool.description

    def test_management_definitions_dict_completeness(self):
        from src.knowledge.tools.management import (
            KNOWLEDGE_MANAGEMENT_TOOL_DEFINITIONS,
            KNOWLEDGE_MANAGEMENT_HANDLERS,
        )

        assert set(KNOWLEDGE_MANAGEMENT_TOOL_DEFINITIONS.keys()) == set(
            KNOWLEDGE_MANAGEMENT_HANDLERS.keys()
        )
        assert len(KNOWLEDGE_MANAGEMENT_TOOL_DEFINITIONS) == 2


# =============================================================================
# Search Handler Tests
# =============================================================================


class TestSearchHandlers:
    """Test search tool handlers with mocked dependencies."""

    @pytest.fixture(autouse=True)
    def setup_mocks(self):
        """Set up mock embedder and store for all search handler tests."""
        from src.knowledge.store.models import ChunkMetadata, SearchResult

        self.mock_results = [
            SearchResult(
                chunk_id="chunk1",
                text="FortiMonitor allows you to create server groups.",
                score=0.92,
                metadata=ChunkMetadata(
                    source_type="pdf",
                    source_name="User Guide",
                    page_number=42,
                    section_heading="Creating Server Groups",
                    breadcrumb="User Guide > Server Groups > Creating",
                ),
            ),
            SearchResult(
                chunk_id="chunk2",
                text="Server groups organize your monitored servers.",
                score=0.85,
                metadata=ChunkMetadata(
                    source_type="pdf",
                    source_name="User Guide",
                    page_number=41,
                    section_heading="Server Groups Overview",
                ),
            ),
        ]

    @pytest.mark.asyncio
    async def test_search_documentation_returns_results(self):
        from src.knowledge.tools import search as search_module

        mock_store = MagicMock()
        mock_store.search.return_value = self.mock_results

        mock_embedder = MagicMock()
        mock_embedder.embed_query.return_value = [0.1] * 384

        search_module._store = mock_store
        search_module._embedder = mock_embedder

        try:
            result = await search_module.handle_search_documentation(
                {"query": "How do I create a server group?"}, None
            )

            assert len(result) == 1
            assert isinstance(result[0], TextContent)
            assert "server group" in result[0].text.lower()
            assert "User Guide" in result[0].text
            mock_embedder.embed_query.assert_called_once()
            mock_store.search.assert_called_once()
        finally:
            search_module._store = None
            search_module._embedder = None

    @pytest.mark.asyncio
    async def test_search_documentation_no_query(self):
        from src.knowledge.tools import search as search_module

        result = await search_module.handle_search_documentation({"query": ""}, None)
        assert "Error" in result[0].text

    @pytest.mark.asyncio
    async def test_search_documentation_empty_results(self):
        from src.knowledge.tools import search as search_module

        mock_store = MagicMock()
        mock_store.search.return_value = []

        mock_embedder = MagicMock()
        mock_embedder.embed_query.return_value = [0.1] * 384

        search_module._store = mock_store
        search_module._embedder = mock_embedder

        try:
            result = await search_module.handle_search_documentation(
                {"query": "nonexistent topic"}, None
            )
            assert "No documentation found" in result[0].text
        finally:
            search_module._store = None
            search_module._embedder = None

    @pytest.mark.asyncio
    async def test_search_api_docs_enhances_query(self):
        from src.knowledge.tools import search as search_module

        mock_store = MagicMock()
        mock_store.search.return_value = self.mock_results

        mock_embedder = MagicMock()
        mock_embedder.embed_query.return_value = [0.1] * 384

        search_module._store = mock_store
        search_module._embedder = mock_embedder

        try:
            await search_module.handle_search_api_docs(
                {"query": "server endpoints"}, None
            )
            # Verify the query was enhanced with "API" prefix
            call_args = mock_embedder.embed_query.call_args[0][0]
            assert "API" in call_args
        finally:
            search_module._store = None
            search_module._embedder = None

    @pytest.mark.asyncio
    async def test_search_troubleshooting_enhances_query(self):
        from src.knowledge.tools import search as search_module

        mock_store = MagicMock()
        mock_store.search.return_value = self.mock_results

        mock_embedder = MagicMock()
        mock_embedder.embed_query.return_value = [0.1] * 384

        search_module._store = mock_store
        search_module._embedder = mock_embedder

        try:
            await search_module.handle_search_troubleshooting(
                {"query": "server not responding"}, None
            )
            call_args = mock_embedder.embed_query.call_args[0][0]
            assert "troubleshooting" in call_args
        finally:
            search_module._store = None
            search_module._embedder = None


# =============================================================================
# Retrieval Handler Tests
# =============================================================================


class TestRetrievalHandlers:
    """Test retrieval tool handlers with mocked store."""

    @pytest.mark.asyncio
    async def test_list_doc_topics_returns_topics(self):
        from src.knowledge.tools import retrieval as retrieval_module

        mock_store = MagicMock()
        mock_store.get_topics.return_value = [
            {"topic": "Creating Server Groups", "source_name": "User Guide", "chunk_count": 5},
            {"topic": "Monitoring Nodes", "source_name": "Admin Guide", "chunk_count": 3},
        ]

        retrieval_module._store = mock_store

        try:
            result = await retrieval_module.handle_list_doc_topics({}, None)
            assert len(result) == 1
            assert "Creating Server Groups" in result[0].text
            assert "Monitoring Nodes" in result[0].text
        finally:
            retrieval_module._store = None

    @pytest.mark.asyncio
    async def test_list_doc_topics_empty(self):
        from src.knowledge.tools import retrieval as retrieval_module

        mock_store = MagicMock()
        mock_store.get_topics.return_value = []

        retrieval_module._store = mock_store

        try:
            result = await retrieval_module.handle_list_doc_topics({}, None)
            assert "No documentation topics found" in result[0].text
        finally:
            retrieval_module._store = None

    @pytest.mark.asyncio
    async def test_get_doc_section_requires_heading(self):
        from src.knowledge.tools import retrieval as retrieval_module

        result = await retrieval_module.handle_get_doc_section(
            {"section_heading": ""}, None
        )
        assert "Error" in result[0].text

    @pytest.mark.asyncio
    async def test_get_doc_section_returns_chunks(self):
        from src.knowledge.tools import retrieval as retrieval_module
        from src.knowledge.store.models import ChunkMetadata, DocumentChunk

        mock_chunks = [
            DocumentChunk(
                chunk_id="c1",
                text="Server groups allow organizing servers.",
                metadata=ChunkMetadata(
                    source_type="pdf",
                    source_name="User Guide",
                    section_heading="Server Groups",
                    breadcrumb="User Guide > Server Groups",
                ),
            ),
        ]

        mock_store = MagicMock()
        mock_store.get_chunks_by_section.return_value = mock_chunks

        retrieval_module._store = mock_store

        try:
            result = await retrieval_module.handle_get_doc_section(
                {"section_heading": "Server Groups"}, None
            )
            assert "Server Groups" in result[0].text
            assert "organizing servers" in result[0].text
        finally:
            retrieval_module._store = None


# =============================================================================
# Management Handler Tests
# =============================================================================


class TestManagementHandlers:
    """Test management tool handlers."""

    @pytest.mark.asyncio
    async def test_get_knowledge_base_status(self):
        from src.knowledge.tools import management as mgmt_module
        from src.knowledge.store.models import KnowledgeBaseStatus

        mock_store = MagicMock()
        mock_store.get_status.return_value = KnowledgeBaseStatus(
            total_chunks=150,
            total_sources=3,
            pdf_sources=2,
            web_sources=1,
            embedding_model="all-MiniLM-L6-v2",
            embedding_dimensions=384,
            store_path="data/vectordb",
            is_initialized=True,
        )

        mgmt_module._store = mock_store

        try:
            result = await mgmt_module.handle_get_knowledge_base_status({}, None)
            assert "150" in result[0].text
            assert "3" in result[0].text
            assert "all-MiniLM-L6-v2" in result[0].text
        finally:
            mgmt_module._store = None

    @pytest.mark.asyncio
    async def test_get_knowledge_base_status_empty(self):
        from src.knowledge.tools import management as mgmt_module
        from src.knowledge.store.models import KnowledgeBaseStatus

        mock_store = MagicMock()
        mock_store.get_status.return_value = KnowledgeBaseStatus(
            total_chunks=0,
            embedding_model="all-MiniLM-L6-v2",
            store_path="data/vectordb",
            is_initialized=True,
        )

        mgmt_module._store = mock_store

        try:
            result = await mgmt_module.handle_get_knowledge_base_status({}, None)
            assert "empty" in result[0].text.lower() or "0" in result[0].text
        finally:
            mgmt_module._store = None
