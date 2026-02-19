"""Knowledge search tools for the MCP server.

Provides search_documentation, search_api_docs, and search_troubleshooting
tools that query the vector store and return relevant documentation chunks.
"""

import logging
from typing import Any, List

from mcp.types import TextContent, Tool

from ..ingestion.embedder import Embedder
from ..store.vector_store import VectorStore

logger = logging.getLogger(__name__)

# Module-level instances (lazy initialized)
_embedder = None
_store = None


def _get_embedder(model_name: str = "all-MiniLM-L6-v2") -> Embedder:
    """Get or create the embedder instance."""
    global _embedder
    if _embedder is None:
        _embedder = Embedder(model_name=model_name)
    return _embedder


def _get_store(db_path: str = "data/vectordb") -> VectorStore:
    """Get or create the vector store instance."""
    global _store
    if _store is None:
        _store = VectorStore(db_path=db_path)
    return _store


def configure(db_path: str, embedding_model: str = "all-MiniLM-L6-v2"):
    """Configure the search tools with specific store path and model.

    Called during server initialization.
    """
    global _store, _embedder
    _store = VectorStore(db_path=db_path)
    _embedder = Embedder(model_name=embedding_model)


def _format_search_results(results, query: str) -> str:
    """Format search results into readable text."""
    if not results:
        return f"No documentation found matching: '{query}'"

    lines = [f"**Documentation Search Results** for: *{query}*\n"]
    lines.append(f"Found {len(results)} relevant sections:\n")

    for i, result in enumerate(results, 1):
        lines.append(f"---\n### Result {i} (relevance: {result.score:.2f})")

        # Source attribution
        source_info = f"**Source**: {result.metadata.source_name}"
        if result.metadata.page_number:
            source_info += f" (page {result.metadata.page_number})"
        lines.append(source_info)

        if result.metadata.section_heading:
            lines.append(f"**Section**: {result.metadata.section_heading}")

        if result.metadata.breadcrumb:
            lines.append(f"**Path**: {result.metadata.breadcrumb}")

        lines.append(f"\n{result.text}\n")

    return "\n".join(lines)


# =============================================================================
# Tool Definitions
# =============================================================================


def search_documentation_tool_definition() -> Tool:
    return Tool(
        name="search_documentation",
        description=(
            "Search FortiMonitor documentation (PDF guides and web docs) for "
            "information about features, configuration, troubleshooting, and best "
            "practices. Returns relevant documentation sections with source attribution."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "The search query. Use natural language questions like "
                        "'How do I create a server group?' or 'What is a compound service?'"
                    ),
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of results to return (default: 5, max: 20)",
                    "default": 5,
                },
                "source_type": {
                    "type": "string",
                    "enum": ["pdf", "web"],
                    "description": "Filter results by source type (optional)",
                },
            },
            "required": ["query"],
        },
    )


def search_api_docs_tool_definition() -> Tool:
    return Tool(
        name="search_api_docs",
        description=(
            "Search FortiMonitor API documentation specifically. Returns "
            "documentation about API endpoints, parameters, request/response "
            "formats, and integration guides."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "API-related search query, e.g., 'server API endpoints' "
                        "or 'authentication methods'"
                    ),
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of results to return (default: 5)",
                    "default": 5,
                },
            },
            "required": ["query"],
        },
    )


def search_troubleshooting_tool_definition() -> Tool:
    return Tool(
        name="search_troubleshooting",
        description=(
            "Search FortiMonitor documentation for troubleshooting guides, "
            "known issues, error resolution, and diagnostic procedures."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "Troubleshooting query, e.g., 'server not responding' "
                        "or 'outage notification not received'"
                    ),
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of results to return (default: 5)",
                    "default": 5,
                },
            },
            "required": ["query"],
        },
    )


# =============================================================================
# Tool Handlers
# =============================================================================


async def handle_search_documentation(
    arguments: dict, client: Any
) -> List[TextContent]:
    """Handle search_documentation tool execution."""
    try:
        query = arguments.get("query", "")
        top_k = min(arguments.get("top_k", 5), 20)
        source_type = arguments.get("source_type")

        if not query:
            return [TextContent(type="text", text="Error: 'query' parameter is required")]

        logger.info(f"Searching documentation: '{query}' (top_k={top_k})")

        embedder = _get_embedder()
        store = _get_store()

        query_embedding = embedder.embed_query(query)
        results = store.search(
            query_embedding=query_embedding,
            top_k=top_k,
            source_type=source_type,
        )

        output = _format_search_results(results, query)
        return [TextContent(type="text", text=output)]

    except Exception as e:
        logger.exception("Error in search_documentation")
        return [TextContent(type="text", text=f"Error searching documentation: {e}")]


async def handle_search_api_docs(
    arguments: dict, client: Any
) -> List[TextContent]:
    """Handle search_api_docs tool execution."""
    try:
        query = arguments.get("query", "")
        top_k = min(arguments.get("top_k", 5), 20)

        if not query:
            return [TextContent(type="text", text="Error: 'query' parameter is required")]

        # Prefix query with API context for better relevance
        enhanced_query = f"API {query}"
        logger.info(f"Searching API docs: '{enhanced_query}' (top_k={top_k})")

        embedder = _get_embedder()
        store = _get_store()

        query_embedding = embedder.embed_query(enhanced_query)
        results = store.search(
            query_embedding=query_embedding,
            top_k=top_k,
        )

        output = _format_search_results(results, query)
        return [TextContent(type="text", text=output)]

    except Exception as e:
        logger.exception("Error in search_api_docs")
        return [TextContent(type="text", text=f"Error searching API docs: {e}")]


async def handle_search_troubleshooting(
    arguments: dict, client: Any
) -> List[TextContent]:
    """Handle search_troubleshooting tool execution."""
    try:
        query = arguments.get("query", "")
        top_k = min(arguments.get("top_k", 5), 20)

        if not query:
            return [TextContent(type="text", text="Error: 'query' parameter is required")]

        # Prefix query with troubleshooting context
        enhanced_query = f"troubleshooting {query}"
        logger.info(f"Searching troubleshooting: '{enhanced_query}' (top_k={top_k})")

        embedder = _get_embedder()
        store = _get_store()

        query_embedding = embedder.embed_query(enhanced_query)
        results = store.search(
            query_embedding=query_embedding,
            top_k=top_k,
        )

        output = _format_search_results(results, query)
        return [TextContent(type="text", text=output)]

    except Exception as e:
        logger.exception("Error in search_troubleshooting")
        return [TextContent(type="text", text=f"Error searching troubleshooting docs: {e}")]


# =============================================================================
# Module Registration (dict pattern)
# =============================================================================

KNOWLEDGE_SEARCH_TOOL_DEFINITIONS = {
    "search_documentation": search_documentation_tool_definition,
    "search_api_docs": search_api_docs_tool_definition,
    "search_troubleshooting": search_troubleshooting_tool_definition,
}

KNOWLEDGE_SEARCH_HANDLERS = {
    "search_documentation": handle_search_documentation,
    "search_api_docs": handle_search_api_docs,
    "search_troubleshooting": handle_search_troubleshooting,
}
