"""Embedding generation using sentence-transformers.

Wraps the sentence-transformers library for generating vector embeddings
from document chunks. Uses all-MiniLM-L6-v2 by default (384 dimensions).
"""

import logging
from typing import Optional

from ..store.models import DocumentChunk

logger = logging.getLogger(__name__)

# Lazy-loaded model instance
_model = None
_model_name = None


def _get_model(model_name: str = "all-MiniLM-L6-v2"):
    """Get or create the sentence-transformers model (lazy singleton).

    Args:
        model_name: Name of the sentence-transformers model.

    Returns:
        The loaded SentenceTransformer model.
    """
    global _model, _model_name

    if _model is not None and _model_name == model_name:
        return _model

    from sentence_transformers import SentenceTransformer

    logger.info(f"Loading embedding model: {model_name}")
    _model = SentenceTransformer(model_name)
    _model_name = model_name
    logger.info(f"Model loaded: {model_name} ({_model.get_sentence_embedding_dimension()} dimensions)")
    return _model


class Embedder:
    """Generate embeddings for document chunks using sentence-transformers."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", batch_size: int = 64):
        """Initialize the embedder.

        Args:
            model_name: Name of the sentence-transformers model.
            batch_size: Number of texts to embed in each batch.
        """
        self.model_name = model_name
        self.batch_size = batch_size
        self._dimensions: Optional[int] = None

    @property
    def dimensions(self) -> int:
        """Get the embedding dimensionality."""
        if self._dimensions is None:
            model = _get_model(self.model_name)
            self._dimensions = model.get_sentence_embedding_dimension()
        return self._dimensions

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts.

        Args:
            texts: List of text strings to embed.

        Returns:
            List of embedding vectors (list of floats).
        """
        if not texts:
            return []

        model = _get_model(self.model_name)

        logger.info(f"Generating embeddings for {len(texts)} texts")
        embeddings = model.encode(
            texts,
            batch_size=self.batch_size,
            show_progress_bar=len(texts) > 100,
            normalize_embeddings=True,
        )

        return [emb.tolist() for emb in embeddings]

    def embed_query(self, query: str) -> list[float]:
        """Generate an embedding for a single query string.

        Args:
            query: The query text.

        Returns:
            Embedding vector as a list of floats.
        """
        model = _get_model(self.model_name)
        embedding = model.encode(
            query,
            normalize_embeddings=True,
        )
        return embedding.tolist()

    def embed_chunks(self, chunks: list[DocumentChunk]) -> list[DocumentChunk]:
        """Add embeddings to document chunks in place.

        Args:
            chunks: List of DocumentChunk objects (embedding field will be set).

        Returns:
            The same chunks list with embeddings populated.
        """
        if not chunks:
            return chunks

        texts = [chunk.text for chunk in chunks]
        embeddings = self.embed_texts(texts)

        for chunk, embedding in zip(chunks, embeddings):
            chunk.embedding = embedding

        logger.info(f"Embedded {len(chunks)} chunks ({self.dimensions} dimensions)")
        return chunks
