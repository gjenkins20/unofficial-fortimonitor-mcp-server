"""LanceDB vector store abstraction for the knowledge base."""

import logging
from pathlib import Path
from typing import Optional

import lancedb
import pyarrow as pa

from .models import ChunkMetadata, DocumentChunk, KnowledgeBaseStatus, SearchResult

logger = logging.getLogger(__name__)

# LanceDB table schema
CHUNKS_TABLE = "chunks"

SCHEMA = pa.schema([
    pa.field("chunk_id", pa.string()),
    pa.field("text", pa.string()),
    pa.field("vector", pa.list_(pa.float32(), 384)),
    pa.field("source_type", pa.string()),
    pa.field("source_name", pa.string()),
    pa.field("source_path", pa.string()),
    pa.field("page_number", pa.int32()),
    pa.field("section_heading", pa.string()),
    pa.field("breadcrumb", pa.string()),
    pa.field("last_modified", pa.string()),
    pa.field("content_hash", pa.string()),
])


class VectorStore:
    """LanceDB-backed vector store for knowledge base chunks."""

    def __init__(self, db_path: str, embedding_dimensions: int = 384):
        """Initialize the vector store.

        Args:
            db_path: Path to the LanceDB database directory.
            embedding_dimensions: Dimensionality of embedding vectors.
        """
        self.db_path = Path(db_path)
        self.embedding_dimensions = embedding_dimensions
        self._db: Optional[lancedb.DBConnection] = None
        self._table = None

    def _ensure_db(self) -> lancedb.DBConnection:
        """Ensure the database connection is established."""
        if self._db is None:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self._db = lancedb.connect(str(self.db_path))
            logger.info(f"Connected to LanceDB at {self.db_path}")
        return self._db

    def _ensure_table(self):
        """Ensure the chunks table exists."""
        if self._table is not None:
            return self._table

        db = self._ensure_db()

        if CHUNKS_TABLE in db.table_names():
            self._table = db.open_table(CHUNKS_TABLE)
            logger.info(f"Opened existing table '{CHUNKS_TABLE}'")
        else:
            # Create empty table with schema
            self._table = db.create_table(CHUNKS_TABLE, schema=SCHEMA)
            logger.info(f"Created new table '{CHUNKS_TABLE}'")

        return self._table

    def add_chunks(self, chunks: list[DocumentChunk]) -> int:
        """Add document chunks to the vector store.

        Args:
            chunks: List of DocumentChunk objects with embeddings.

        Returns:
            Number of chunks added.
        """
        if not chunks:
            return 0

        table = self._ensure_table()

        records = []
        for chunk in chunks:
            if chunk.embedding is None:
                logger.warning(f"Skipping chunk {chunk.chunk_id}: no embedding")
                continue

            records.append({
                "chunk_id": chunk.chunk_id,
                "text": chunk.text,
                "vector": chunk.embedding,
                "source_type": chunk.metadata.source_type,
                "source_name": chunk.metadata.source_name,
                "source_path": chunk.metadata.source_path or "",
                "page_number": chunk.metadata.page_number or 0,
                "section_heading": chunk.metadata.section_heading or "",
                "breadcrumb": chunk.metadata.breadcrumb or "",
                "last_modified": chunk.metadata.last_modified or "",
                "content_hash": chunk.metadata.content_hash or "",
            })

        if records:
            table.add(records)
            logger.info(f"Added {len(records)} chunks to vector store")

        return len(records)

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        source_type: Optional[str] = None,
    ) -> list[SearchResult]:
        """Search for similar chunks using vector similarity.

        Args:
            query_embedding: The query vector.
            top_k: Number of results to return.
            source_type: Optional filter by source type ('pdf' or 'web').

        Returns:
            List of SearchResult objects ranked by similarity.
        """
        table = self._ensure_table()

        query = table.search(query_embedding).limit(top_k)

        if source_type:
            query = query.where(f"source_type = '{source_type}'")

        try:
            results = query.to_pandas()
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []

        search_results = []
        for _, row in results.iterrows():
            metadata = ChunkMetadata(
                source_type=row.get("source_type", ""),
                source_name=row.get("source_name", ""),
                source_path=row.get("source_path") or None,
                page_number=int(row["page_number"]) if row.get("page_number") else None,
                section_heading=row.get("section_heading") or None,
                breadcrumb=row.get("breadcrumb") or None,
                last_modified=row.get("last_modified") or None,
                content_hash=row.get("content_hash") or None,
            )

            search_results.append(SearchResult(
                chunk_id=row["chunk_id"],
                text=row["text"],
                score=float(1.0 - row.get("_distance", 0.0)),
                metadata=metadata,
            ))

        return search_results

    def delete_by_source(self, source_name: str) -> int:
        """Delete all chunks from a specific source.

        Args:
            source_name: Name of the source to delete.

        Returns:
            Number of chunks deleted (approximate).
        """
        table = self._ensure_table()
        initial_count = table.count_rows()
        table.delete(f"source_name = '{source_name}'")
        final_count = table.count_rows()
        deleted = initial_count - final_count
        logger.info(f"Deleted {deleted} chunks from source '{source_name}'")
        return deleted

    def get_status(self, embedding_model: str = "") -> KnowledgeBaseStatus:
        """Get current status of the knowledge base.

        Args:
            embedding_model: Name of the embedding model for status display.

        Returns:
            KnowledgeBaseStatus with current statistics.
        """
        try:
            table = self._ensure_table()
            df = table.to_pandas()

            total_chunks = len(df)
            if total_chunks == 0:
                return KnowledgeBaseStatus(
                    store_path=str(self.db_path),
                    embedding_model=embedding_model,
                    embedding_dimensions=self.embedding_dimensions,
                    is_initialized=True,
                )

            unique_sources = df["source_name"].nunique()
            pdf_sources = df[df["source_type"] == "pdf"]["source_name"].nunique()
            web_sources = df[df["source_type"] == "web"]["source_name"].nunique()

            return KnowledgeBaseStatus(
                total_chunks=total_chunks,
                total_sources=unique_sources,
                pdf_sources=pdf_sources,
                web_sources=web_sources,
                embedding_model=embedding_model,
                embedding_dimensions=self.embedding_dimensions,
                store_path=str(self.db_path),
                is_initialized=True,
            )
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            return KnowledgeBaseStatus(
                store_path=str(self.db_path),
                embedding_model=embedding_model,
                is_initialized=False,
            )

    def has_source(self, source_name: str) -> bool:
        """Check if a source has already been ingested.

        Args:
            source_name: Name of the source to check.

        Returns:
            True if the source exists in the store.
        """
        try:
            table = self._ensure_table()
            df = table.search().where(
                f"source_name = '{source_name}'"
            ).limit(1).to_pandas()
            return len(df) > 0
        except Exception:
            return False

    def get_topics(self) -> list[dict]:
        """Get a list of unique section headings (topics) in the knowledge base.

        Returns:
            List of dicts with 'topic', 'source_name', 'chunk_count' keys.
        """
        try:
            table = self._ensure_table()
            df = table.to_pandas()

            if len(df) == 0:
                return []

            topics = (
                df[df["section_heading"] != ""]
                .groupby(["section_heading", "source_name"])
                .size()
                .reset_index(name="chunk_count")
                .rename(columns={"section_heading": "topic"})
                .to_dict("records")
            )
            return topics
        except Exception as e:
            logger.error(f"Error getting topics: {e}")
            return []

    def get_chunks_by_section(
        self, section_heading: str, source_name: Optional[str] = None
    ) -> list[DocumentChunk]:
        """Get all chunks from a specific section.

        Args:
            section_heading: The section heading to filter by.
            source_name: Optional source name filter.

        Returns:
            List of DocumentChunk objects from that section.
        """
        try:
            table = self._ensure_table()
            where_clause = f"section_heading = '{section_heading}'"
            if source_name:
                where_clause += f" AND source_name = '{source_name}'"

            df = table.search().where(where_clause).limit(100).to_pandas()

            chunks = []
            for _, row in df.iterrows():
                metadata = ChunkMetadata(
                    source_type=row.get("source_type", ""),
                    source_name=row.get("source_name", ""),
                    source_path=row.get("source_path") or None,
                    page_number=int(row["page_number"]) if row.get("page_number") else None,
                    section_heading=row.get("section_heading") or None,
                    breadcrumb=row.get("breadcrumb") or None,
                )
                chunks.append(DocumentChunk(
                    chunk_id=row["chunk_id"],
                    text=row["text"],
                    metadata=metadata,
                ))
            return chunks
        except Exception as e:
            logger.error(f"Error getting chunks by section: {e}")
            return []
