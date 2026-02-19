"""Knowledge base management tools for the MCP server.

Provides refresh_knowledge_base and get_knowledge_base_status tools
for managing the documentation knowledge base.
"""

import logging
from pathlib import Path
from typing import Any, List

from mcp.types import TextContent, Tool

from ..ingestion.pipeline import IngestionPipeline
from ..store.vector_store import VectorStore

logger = logging.getLogger(__name__)

# Module-level instances
_store = None
_sources_file = None
_embedding_model = None


def _get_store(db_path: str = "data/vectordb") -> VectorStore:
    """Get or create the vector store instance."""
    global _store
    if _store is None:
        _store = VectorStore(db_path=db_path)
    return _store


def configure(
    db_path: str,
    sources_file: str = "data/sources.yaml",
    embedding_model: str = "all-MiniLM-L6-v2",
):
    """Configure management tools."""
    global _store, _sources_file, _embedding_model
    _store = VectorStore(db_path=db_path)
    _sources_file = sources_file
    _embedding_model = embedding_model


# =============================================================================
# Tool Definitions
# =============================================================================


def refresh_knowledge_base_tool_definition() -> Tool:
    return Tool(
        name="refresh_knowledge_base",
        description=(
            "Refresh the knowledge base by re-ingesting documentation sources. "
            "Can ingest all sources or filter by type (pdf/web). Use 'force' to "
            "re-ingest sources that were already processed."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "source_type": {
                    "type": "string",
                    "enum": ["pdf", "web"],
                    "description": "Only refresh this source type (optional, default: all)",
                },
                "force": {
                    "type": "boolean",
                    "description": "Force re-ingestion even for already-processed sources (default: false)",
                    "default": False,
                },
            },
        },
    )


def get_knowledge_base_status_tool_definition() -> Tool:
    return Tool(
        name="get_knowledge_base_status",
        description=(
            "Get the current status of the knowledge base including total chunks, "
            "number of sources, embedding model info, and store path."
        ),
        inputSchema={
            "type": "object",
            "properties": {},
        },
    )


# =============================================================================
# Tool Handlers
# =============================================================================


async def handle_refresh_knowledge_base(
    arguments: dict, client: Any
) -> List[TextContent]:
    """Handle refresh_knowledge_base tool execution."""
    try:
        source_type = arguments.get("source_type")
        force = arguments.get("force", False)

        global _sources_file, _embedding_model

        sources_file = _sources_file or "data/sources.yaml"
        embedding_model = _embedding_model or "all-MiniLM-L6-v2"

        if not Path(sources_file).exists():
            return [TextContent(
                type="text",
                text=(
                    f"Error: Sources config not found at '{sources_file}'. "
                    "Create a data/sources.yaml file with PDF and web source definitions."
                ),
            )]

        logger.info(
            f"Refreshing knowledge base (source_type={source_type}, force={force})"
        )

        store = _get_store()
        pipeline = IngestionPipeline(
            vector_store=store,
            embedding_model=embedding_model,
        )

        result = pipeline.ingest_from_config(
            config_path=sources_file,
            source_filter=source_type,
            force=force,
        )

        lines = ["**Knowledge Base Refresh Complete**\n"]
        lines.append(f"- Sources processed: {result['sources_processed']}")
        lines.append(f"- Total chunks added: {result['total_chunks']}")

        if result["errors"]:
            lines.append(f"\n**Errors** ({len(result['errors'])}):")
            for err in result["errors"]:
                lines.append(f"- {err['source']}: {err['error']}")

        # Show updated status
        status = store.get_status(embedding_model=embedding_model)
        lines.append(f"\n**Updated Status**:")
        lines.append(f"- Total chunks in store: {status.total_chunks}")
        lines.append(f"- Total sources: {status.total_sources}")

        return [TextContent(type="text", text="\n".join(lines))]

    except Exception as e:
        logger.exception("Error refreshing knowledge base")
        return [TextContent(type="text", text=f"Error refreshing knowledge base: {e}")]


async def handle_get_knowledge_base_status(
    arguments: dict, client: Any
) -> List[TextContent]:
    """Handle get_knowledge_base_status tool execution."""
    try:
        global _embedding_model
        embedding_model = _embedding_model or "all-MiniLM-L6-v2"

        logger.info("Getting knowledge base status")

        store = _get_store()
        status = store.get_status(embedding_model=embedding_model)

        lines = ["**Knowledge Base Status**\n"]
        lines.append(f"- **Initialized**: {'Yes' if status.is_initialized else 'No'}")
        lines.append(f"- **Store path**: {status.store_path}")
        lines.append(f"- **Embedding model**: {status.embedding_model}")
        lines.append(f"- **Embedding dimensions**: {status.embedding_dimensions}")
        lines.append(f"- **Total chunks**: {status.total_chunks}")
        lines.append(f"- **Total sources**: {status.total_sources}")
        lines.append(f"- **PDF sources**: {status.pdf_sources}")
        lines.append(f"- **Web sources**: {status.web_sources}")

        if status.total_chunks == 0:
            lines.append(
                "\n*The knowledge base is empty. Use 'refresh_knowledge_base' "
                "to ingest documentation sources.*"
            )

        return [TextContent(type="text", text="\n".join(lines))]

    except Exception as e:
        logger.exception("Error getting knowledge base status")
        return [TextContent(type="text", text=f"Error getting status: {e}")]


# =============================================================================
# Module Registration (dict pattern)
# =============================================================================

KNOWLEDGE_MANAGEMENT_TOOL_DEFINITIONS = {
    "refresh_knowledge_base": refresh_knowledge_base_tool_definition,
    "get_knowledge_base_status": get_knowledge_base_status_tool_definition,
}

KNOWLEDGE_MANAGEMENT_HANDLERS = {
    "refresh_knowledge_base": handle_refresh_knowledge_base,
    "get_knowledge_base_status": handle_get_knowledge_base_status,
}
