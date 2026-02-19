"""Tests for Knowledge Layer ingestion pipeline.

Tests PDF parsing, chunking, and pipeline orchestration
using mock dependencies (no actual PDF files or ML models needed).
"""

import pytest
from unittest.mock import MagicMock, patch, mock_open

from src.knowledge.store.models import ChunkMetadata, DocumentChunk


# =============================================================================
# Chunker Tests
# =============================================================================


class TestChunker:
    """Test the heading-aware text chunker."""

    def test_chunker_basic_text(self):
        from src.knowledge.ingestion.chunker import Chunker

        chunker = Chunker(chunk_size=100, chunk_overlap=10, min_chunk_size=5)
        text = "This is a test paragraph with some content that should be chunked."

        chunks = chunker.chunk_text(
            text=text,
            source_type="pdf",
            source_name="test.pdf",
        )

        assert len(chunks) >= 1
        assert all(isinstance(c, DocumentChunk) for c in chunks)
        assert all(c.metadata.source_type == "pdf" for c in chunks)
        assert all(c.metadata.source_name == "test.pdf" for c in chunks)

    def test_chunker_preserves_headings(self):
        from src.knowledge.ingestion.chunker import Chunker

        chunker = Chunker(chunk_size=200, chunk_overlap=10, min_chunk_size=5)
        text = """# Main Title

This is the introduction paragraph.

## Section One

Content for section one goes here with enough text to matter.

## Section Two

Content for section two goes here with enough text to matter.
"""

        chunks = chunker.chunk_text(
            text=text,
            source_type="pdf",
            source_name="test.pdf",
        )

        # Should have chunks from different sections
        assert len(chunks) >= 1
        headings = [c.metadata.section_heading for c in chunks]
        assert any(h for h in headings if h)  # At least one heading captured

    def test_chunker_builds_breadcrumbs(self):
        from src.knowledge.ingestion.chunker import Chunker

        chunker = Chunker(chunk_size=200, chunk_overlap=10, min_chunk_size=5)
        text = """# Top Level

## Mid Level

### Deep Level

Some content at the deep level that should have a full breadcrumb path.
"""

        chunks = chunker.chunk_text(
            text=text,
            source_type="pdf",
            source_name="test.pdf",
        )

        breadcrumbs = [c.metadata.breadcrumb for c in chunks if c.metadata.breadcrumb]
        assert len(breadcrumbs) >= 1
        # At least one breadcrumb should have multiple levels
        assert any(">" in b for b in breadcrumbs)

    def test_chunker_generates_content_hash(self):
        from src.knowledge.ingestion.chunker import Chunker

        chunker = Chunker(chunk_size=200, chunk_overlap=10, min_chunk_size=5)
        text = "A paragraph with enough content to create a chunk."

        chunks = chunker.chunk_text(
            text=text,
            source_type="pdf",
            source_name="test.pdf",
        )

        assert len(chunks) >= 1
        for chunk in chunks:
            assert chunk.metadata.content_hash
            assert len(chunk.metadata.content_hash) == 16  # SHA-256 truncated to 16

    def test_chunker_unique_chunk_ids(self):
        from src.knowledge.ingestion.chunker import Chunker

        chunker = Chunker(chunk_size=50, chunk_overlap=10, min_chunk_size=5)
        text = """# Section A

First section content paragraph one.

First section content paragraph two.

# Section B

Second section content paragraph.
"""

        chunks = chunker.chunk_text(
            text=text,
            source_type="pdf",
            source_name="test.pdf",
        )

        ids = [c.chunk_id for c in chunks]
        assert len(ids) == len(set(ids)), "Chunk IDs should be unique"

    def test_chunker_handles_empty_text(self):
        from src.knowledge.ingestion.chunker import Chunker

        chunker = Chunker()
        chunks = chunker.chunk_text(
            text="",
            source_type="pdf",
            source_name="test.pdf",
        )
        assert chunks == []

    def test_chunker_respects_min_chunk_size(self):
        from src.knowledge.ingestion.chunker import Chunker

        chunker = Chunker(chunk_size=200, chunk_overlap=10, min_chunk_size=50)
        text = "Tiny."  # Only 1 token

        chunks = chunker.chunk_text(
            text=text,
            source_type="pdf",
            source_name="test.pdf",
        )
        # Should be empty because the text is below min_chunk_size
        assert chunks == []


# =============================================================================
# Embedder Tests
# =============================================================================


class TestEmbedder:
    """Test the embedding wrapper (with mocked sentence-transformers)."""

    @patch("src.knowledge.ingestion.embedder._get_model")
    def test_embed_texts(self, mock_get_model):
        import numpy as np
        from src.knowledge.ingestion.embedder import Embedder

        mock_model = MagicMock()
        mock_model.encode.return_value = np.random.rand(3, 384).astype(np.float32)
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_get_model.return_value = mock_model

        embedder = Embedder()
        result = embedder.embed_texts(["text1", "text2", "text3"])

        assert len(result) == 3
        assert all(len(emb) == 384 for emb in result)
        mock_model.encode.assert_called_once()

    @patch("src.knowledge.ingestion.embedder._get_model")
    def test_embed_query(self, mock_get_model):
        import numpy as np
        from src.knowledge.ingestion.embedder import Embedder

        mock_model = MagicMock()
        mock_model.encode.return_value = np.random.rand(384).astype(np.float32)
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_get_model.return_value = mock_model

        embedder = Embedder()
        result = embedder.embed_query("test query")

        assert len(result) == 384

    @patch("src.knowledge.ingestion.embedder._get_model")
    def test_embed_chunks(self, mock_get_model):
        import numpy as np
        from src.knowledge.ingestion.embedder import Embedder

        mock_model = MagicMock()
        mock_model.encode.return_value = np.random.rand(2, 384).astype(np.float32)
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_get_model.return_value = mock_model

        embedder = Embedder()

        chunks = [
            DocumentChunk(
                chunk_id="c1",
                text="Chunk one text",
                metadata=ChunkMetadata(source_type="pdf", source_name="test"),
            ),
            DocumentChunk(
                chunk_id="c2",
                text="Chunk two text",
                metadata=ChunkMetadata(source_type="pdf", source_name="test"),
            ),
        ]

        result = embedder.embed_chunks(chunks)
        assert len(result) == 2
        assert result[0].embedding is not None
        assert result[1].embedding is not None
        assert len(result[0].embedding) == 384

    @patch("src.knowledge.ingestion.embedder._get_model")
    def test_embed_empty_list(self, mock_get_model):
        from src.knowledge.ingestion.embedder import Embedder

        embedder = Embedder()
        result = embedder.embed_texts([])
        assert result == []


# =============================================================================
# Store Models Tests
# =============================================================================


class TestStoreModels:
    """Test Pydantic models for the knowledge base."""

    def test_chunk_metadata_defaults(self):
        meta = ChunkMetadata(source_type="pdf", source_name="guide.pdf")
        assert meta.source_type == "pdf"
        assert meta.source_name == "guide.pdf"
        assert meta.page_number is None
        assert meta.section_heading is None

    def test_document_chunk_creation(self):
        chunk = DocumentChunk(
            chunk_id="test-id",
            text="Sample text",
            metadata=ChunkMetadata(source_type="web", source_name="docs.example.com"),
        )
        assert chunk.chunk_id == "test-id"
        assert chunk.text == "Sample text"
        assert chunk.embedding is None

    def test_search_result_creation(self):
        from src.knowledge.store.models import SearchResult

        result = SearchResult(
            chunk_id="r1",
            text="Result text",
            score=0.95,
            metadata=ChunkMetadata(source_type="pdf", source_name="guide.pdf"),
        )
        assert result.score == 0.95

    def test_knowledge_base_status_defaults(self):
        from src.knowledge.store.models import KnowledgeBaseStatus

        status = KnowledgeBaseStatus()
        assert status.total_chunks == 0
        assert status.is_initialized is False


# =============================================================================
# PDF Parser Tests (mocked)
# =============================================================================


class TestPDFParser:
    """Test PDF parser with mocked PyMuPDF."""

    def test_parse_nonexistent_file(self):
        from src.knowledge.ingestion.pdf_parser import PDFParser

        parser = PDFParser()
        with pytest.raises(FileNotFoundError):
            parser.parse("/nonexistent/file.pdf")

    def test_parse_non_pdf_file(self, tmp_path):
        from src.knowledge.ingestion.pdf_parser import PDFParser

        text_file = tmp_path / "test.txt"
        text_file.write_text("not a pdf")

        parser = PDFParser()
        with pytest.raises(ValueError, match="Not a PDF"):
            parser.parse(str(text_file))

    def test_get_page_count_nonexistent(self):
        from src.knowledge.ingestion.pdf_parser import PDFParser

        parser = PDFParser()
        with pytest.raises(FileNotFoundError):
            parser.get_page_count("/nonexistent/file.pdf")
