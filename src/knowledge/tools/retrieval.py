"""Knowledge retrieval tools for the MCP server.

Provides structured retrieval tools: get_doc_section, list_doc_topics,
and get_release_notes for navigating the knowledge base.
"""

import logging
from typing import Any, List

from mcp.types import TextContent, Tool

from ..store.vector_store import VectorStore

logger = logging.getLogger(__name__)

# Module-level store instance (shared with search.py via configure)
_store = None


def _get_store(db_path: str = "data/vectordb") -> VectorStore:
    """Get or create the vector store instance."""
    global _store
    if _store is None:
        _store = VectorStore(db_path=db_path)
    return _store


def configure(db_path: str):
    """Configure retrieval tools with the store path."""
    global _store
    _store = VectorStore(db_path=db_path)


# =============================================================================
# Tool Definitions
# =============================================================================


def get_doc_section_tool_definition() -> Tool:
    return Tool(
        name="get_doc_section",
        description=(
            "Retrieve the full content of a specific documentation section by heading. "
            "Use list_doc_topics first to discover available sections, then retrieve "
            "the one you need."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "section_heading": {
                    "type": "string",
                    "description": "The section heading to retrieve (e.g., 'Creating Server Groups')",
                },
                "source_name": {
                    "type": "string",
                    "description": "Optional: limit to a specific source document",
                },
            },
            "required": ["section_heading"],
        },
    )


def list_doc_topics_tool_definition() -> Tool:
    return Tool(
        name="list_doc_topics",
        description=(
            "List all available documentation topics (section headings) in the "
            "knowledge base. Useful for discovering what documentation is available "
            "before searching."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "source_filter": {
                    "type": "string",
                    "description": "Optional: filter topics by source name",
                },
            },
        },
    )


def get_release_notes_tool_definition() -> Tool:
    return Tool(
        name="get_release_notes",
        description=(
            "Search for release notes and changelog information in the "
            "FortiMonitor documentation. Returns sections related to version "
            "changes, new features, and known issues."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "version": {
                    "type": "string",
                    "description": "Optional: specific version to look for (e.g., '25.3', '26.1')",
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of results to return (default: 5)",
                    "default": 5,
                },
            },
        },
    )


# =============================================================================
# Tool Handlers
# =============================================================================


async def handle_get_doc_section(
    arguments: dict, client: Any
) -> List[TextContent]:
    """Handle get_doc_section tool execution."""
    try:
        section_heading = arguments.get("section_heading", "")
        source_name = arguments.get("source_name")

        if not section_heading:
            return [TextContent(
                type="text",
                text="Error: 'section_heading' parameter is required",
            )]

        logger.info(f"Retrieving section: '{section_heading}'")

        store = _get_store()
        chunks = store.get_chunks_by_section(section_heading, source_name)

        if not chunks:
            return [TextContent(
                type="text",
                text=f"No documentation section found with heading: '{section_heading}'",
            )]

        lines = [f"**Documentation Section**: {section_heading}\n"]

        if chunks[0].metadata.source_name:
            lines.append(f"**Source**: {chunks[0].metadata.source_name}")
        if chunks[0].metadata.breadcrumb:
            lines.append(f"**Path**: {chunks[0].metadata.breadcrumb}")

        lines.append(f"\n---\n")

        for chunk in chunks:
            lines.append(chunk.text)
            lines.append("")  # blank line between chunks

        return [TextContent(type="text", text="\n".join(lines))]

    except Exception as e:
        logger.exception("Error in get_doc_section")
        return [TextContent(type="text", text=f"Error retrieving section: {e}")]


async def handle_list_doc_topics(
    arguments: dict, client: Any
) -> List[TextContent]:
    """Handle list_doc_topics tool execution."""
    try:
        source_filter = arguments.get("source_filter")

        logger.info("Listing documentation topics")

        store = _get_store()
        topics = store.get_topics()

        if source_filter:
            topics = [t for t in topics if source_filter.lower() in t["source_name"].lower()]

        if not topics:
            msg = "No documentation topics found"
            if source_filter:
                msg += f" for source: '{source_filter}'"
            msg += ". The knowledge base may need to be initialized with 'refresh_knowledge_base'."
            return [TextContent(type="text", text=msg)]

        # Group topics by source
        by_source: dict[str, list] = {}
        for topic in topics:
            source = topic["source_name"]
            if source not in by_source:
                by_source[source] = []
            by_source[source].append(topic)

        lines = [f"**Documentation Topics** ({len(topics)} sections)\n"]

        for source, source_topics in sorted(by_source.items()):
            lines.append(f"\n### {source}")
            for t in sorted(source_topics, key=lambda x: x["topic"]):
                lines.append(f"- {t['topic']} ({t['chunk_count']} chunks)")

        return [TextContent(type="text", text="\n".join(lines))]

    except Exception as e:
        logger.exception("Error in list_doc_topics")
        return [TextContent(type="text", text=f"Error listing topics: {e}")]


async def handle_get_release_notes(
    arguments: dict, client: Any
) -> List[TextContent]:
    """Handle get_release_notes tool execution."""
    try:
        version = arguments.get("version", "")
        top_k = min(arguments.get("top_k", 5), 20)

        # Build search query for release notes
        query = "release notes changelog new features"
        if version:
            query = f"release notes version {version} changelog"

        logger.info(f"Searching release notes: '{query}'")

        # Use the search module's embedder
        from .search import _get_embedder

        embedder = _get_embedder()
        store = _get_store()

        query_embedding = embedder.embed_query(query)
        results = store.search(
            query_embedding=query_embedding,
            top_k=top_k,
        )

        if not results:
            msg = "No release notes found in the knowledge base"
            if version:
                msg += f" for version {version}"
            return [TextContent(type="text", text=msg)]

        lines = ["**Release Notes Search Results**\n"]
        if version:
            lines[0] = f"**Release Notes for version {version}**\n"

        for i, result in enumerate(results, 1):
            lines.append(f"---\n### Result {i} (relevance: {result.score:.2f})")
            lines.append(f"**Source**: {result.metadata.source_name}")
            if result.metadata.section_heading:
                lines.append(f"**Section**: {result.metadata.section_heading}")
            lines.append(f"\n{result.text}\n")

        return [TextContent(type="text", text="\n".join(lines))]

    except Exception as e:
        logger.exception("Error in get_release_notes")
        return [TextContent(type="text", text=f"Error searching release notes: {e}")]


# =============================================================================
# Module Registration (dict pattern)
# =============================================================================

KNOWLEDGE_RETRIEVAL_TOOL_DEFINITIONS = {
    "get_doc_section": get_doc_section_tool_definition,
    "list_doc_topics": list_doc_topics_tool_definition,
    "get_release_notes": get_release_notes_tool_definition,
}

KNOWLEDGE_RETRIEVAL_HANDLERS = {
    "get_doc_section": handle_get_doc_section,
    "list_doc_topics": handle_list_doc_topics,
    "get_release_notes": handle_get_release_notes,
}
