"""Pydantic models for knowledge base chunks and metadata."""

from typing import Optional
from pydantic import BaseModel, Field


class ChunkMetadata(BaseModel):
    """Metadata associated with a document chunk."""

    source_type: str = Field(
        description="Type of source: 'pdf' or 'web'"
    )
    source_name: str = Field(
        description="Filename or URL of the source document"
    )
    source_path: Optional[str] = Field(
        default=None,
        description="Local file path or full URL"
    )
    page_number: Optional[int] = Field(
        default=None,
        description="Page number in PDF (1-indexed), None for web"
    )
    section_heading: Optional[str] = Field(
        default=None,
        description="Nearest heading above the chunk"
    )
    breadcrumb: Optional[str] = Field(
        default=None,
        description="Hierarchical path (e.g., 'User Guide > Server Groups > Creating')"
    )
    last_modified: Optional[str] = Field(
        default=None,
        description="Last modified date of the source"
    )
    content_hash: Optional[str] = Field(
        default=None,
        description="SHA-256 hash of the chunk text for deduplication"
    )


class DocumentChunk(BaseModel):
    """A chunk of text from a documentation source with its metadata."""

    chunk_id: str = Field(
        description="Unique identifier for the chunk"
    )
    text: str = Field(
        description="The chunk text content"
    )
    metadata: ChunkMetadata = Field(
        description="Metadata about the chunk's origin"
    )
    embedding: Optional[list[float]] = Field(
        default=None,
        description="Vector embedding of the chunk text"
    )


class SearchResult(BaseModel):
    """A search result from the vector store."""

    chunk_id: str = Field(
        description="ID of the matching chunk"
    )
    text: str = Field(
        description="Text content of the matching chunk"
    )
    score: float = Field(
        description="Similarity score (higher is more relevant)"
    )
    metadata: ChunkMetadata = Field(
        description="Source metadata for attribution"
    )


class KnowledgeBaseStatus(BaseModel):
    """Status information about the knowledge base."""

    total_chunks: int = Field(
        default=0, description="Total number of chunks in the store"
    )
    total_sources: int = Field(
        default=0, description="Number of unique sources indexed"
    )
    pdf_sources: int = Field(
        default=0, description="Number of PDF sources"
    )
    web_sources: int = Field(
        default=0, description="Number of web sources"
    )
    embedding_model: str = Field(
        default="", description="Name of the embedding model in use"
    )
    embedding_dimensions: int = Field(
        default=0, description="Dimensionality of embeddings"
    )
    store_path: str = Field(
        default="", description="Path to the vector store"
    )
    is_initialized: bool = Field(
        default=False, description="Whether the store has been initialized"
    )
