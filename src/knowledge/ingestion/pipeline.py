"""Ingestion pipeline orchestrator.

Coordinates the full flow: fetch source > parse > chunk > embed > store.
Supports PDF, Markdown, and web content sources.
"""

import logging
import tempfile
from pathlib import Path
from typing import Optional

import requests
import yaml

from .chunker import Chunker
from .embedder import Embedder
from .pdf_parser import PDFParser
from ..store.vector_store import VectorStore

logger = logging.getLogger(__name__)


class IngestionPipeline:
    """Orchestrates ingestion of documentation sources into the vector store."""

    def __init__(
        self,
        vector_store: VectorStore,
        embedding_model: str = "all-MiniLM-L6-v2",
        chunk_size: int = 800,
        chunk_overlap: int = 100,
    ):
        """Initialize the pipeline.

        Args:
            vector_store: The vector store to write chunks to.
            embedding_model: Name of the sentence-transformers model.
            chunk_size: Target chunk size in tokens.
            chunk_overlap: Overlap between chunks in tokens.
        """
        self.store = vector_store
        self.pdf_parser = PDFParser()
        self.chunker = Chunker(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        self.embedder = Embedder(model_name=embedding_model)

    def ingest_pdf(
        self,
        pdf_path: str,
        source_name: Optional[str] = None,
        force: bool = False,
    ) -> int:
        """Ingest a local PDF file.

        Args:
            pdf_path: Path to the PDF file.
            source_name: Display name for the source (defaults to filename).
            force: If True, re-ingest even if source already exists.

        Returns:
            Number of chunks stored.
        """
        path = Path(pdf_path)
        source_name = source_name or path.name

        if not force and self.store.has_source(source_name):
            logger.info(f"Source '{source_name}' already ingested, skipping")
            return 0

        if not force:
            # Delete existing chunks if re-ingesting
            pass
        else:
            self.store.delete_by_source(source_name)

        # Parse PDF to Markdown
        markdown_text = self.pdf_parser.parse(pdf_path)

        # Chunk the text
        chunks = self.chunker.chunk_text(
            text=markdown_text,
            source_type="pdf",
            source_name=source_name,
            source_path=str(path.absolute()),
        )

        if not chunks:
            logger.warning(f"No chunks generated from {source_name}")
            return 0

        # Generate embeddings
        chunks = self.embedder.embed_chunks(chunks)

        # Store in vector database
        count = self.store.add_chunks(chunks)
        logger.info(f"Ingested {count} chunks from PDF: {source_name}")
        return count

    def ingest_pdf_url(
        self,
        url: str,
        source_name: Optional[str] = None,
        force: bool = False,
    ) -> int:
        """Download and ingest a PDF from a URL.

        Args:
            url: URL of the PDF file.
            source_name: Display name for the source.
            force: If True, re-ingest even if source already exists.

        Returns:
            Number of chunks stored.
        """
        source_name = source_name or url.split("/")[-1]

        if not force and self.store.has_source(source_name):
            logger.info(f"Source '{source_name}' already ingested, skipping")
            return 0

        logger.info(f"Downloading PDF: {url}")
        response = requests.get(url, timeout=120)
        response.raise_for_status()

        # Save to temp file
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(response.content)
            tmp_path = tmp.name

        try:
            if force:
                self.store.delete_by_source(source_name)

            # Parse, chunk, embed, store
            markdown_text = self.pdf_parser.parse(tmp_path)

            chunks = self.chunker.chunk_text(
                text=markdown_text,
                source_type="pdf",
                source_name=source_name,
                source_path=url,
            )

            if not chunks:
                logger.warning(f"No chunks generated from {source_name}")
                return 0

            chunks = self.embedder.embed_chunks(chunks)
            count = self.store.add_chunks(chunks)
            logger.info(f"Ingested {count} chunks from PDF URL: {source_name}")
            return count
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def ingest_markdown(
        self,
        md_path: str,
        source_name: Optional[str] = None,
        force: bool = False,
    ) -> int:
        """Ingest a local Markdown file.

        Args:
            md_path: Path to the Markdown file.
            source_name: Display name for the source (defaults to filename).
            force: If True, re-ingest even if source already exists.

        Returns:
            Number of chunks stored.
        """
        path = Path(md_path)
        source_name = source_name or path.name

        if not path.exists():
            raise FileNotFoundError(f"Markdown file not found: {md_path}")

        if not force and self.store.has_source(source_name):
            logger.info(f"Source '{source_name}' already ingested, skipping")
            return 0

        if force:
            self.store.delete_by_source(source_name)

        markdown_text = path.read_text(encoding="utf-8")

        chunks = self.chunker.chunk_text(
            text=markdown_text,
            source_type="markdown",
            source_name=source_name,
            source_path=str(path.absolute()),
        )

        if not chunks:
            logger.warning(f"No chunks generated from {source_name}")
            return 0

        chunks = self.embedder.embed_chunks(chunks)
        count = self.store.add_chunks(chunks)
        logger.info(f"Ingested {count} chunks from Markdown: {source_name}")
        return count

    def ingest_web(
        self,
        url: str,
        markdown_text: str,
        source_name: Optional[str] = None,
        force: bool = False,
    ) -> int:
        """Ingest pre-crawled web content (Markdown).

        Args:
            url: Original URL of the page.
            markdown_text: Pre-processed Markdown content.
            source_name: Display name for the source.
            force: If True, re-ingest even if source already exists.

        Returns:
            Number of chunks stored.
        """
        source_name = source_name or url

        if not force and self.store.has_source(source_name):
            logger.info(f"Source '{source_name}' already ingested, skipping")
            return 0

        if force:
            self.store.delete_by_source(source_name)

        chunks = self.chunker.chunk_text(
            text=markdown_text,
            source_type="web",
            source_name=source_name,
            source_path=url,
        )

        if not chunks:
            logger.warning(f"No chunks generated from {source_name}")
            return 0

        chunks = self.embedder.embed_chunks(chunks)
        count = self.store.add_chunks(chunks)
        logger.info(f"Ingested {count} chunks from web: {source_name}")
        return count

    def ingest_from_config(
        self,
        config_path: str,
        source_filter: Optional[str] = None,
        force: bool = False,
    ) -> dict:
        """Ingest all sources defined in a YAML configuration file.

        Args:
            config_path: Path to the sources.yaml file.
            source_filter: Only ingest sources matching this type ('pdf' or 'web').
            force: If True, re-ingest all sources.

        Returns:
            Dict with 'total_chunks', 'sources_processed', 'errors' keys.
        """
        config = Path(config_path)
        if not config.exists():
            raise FileNotFoundError(f"Config not found: {config_path}")

        with open(config_path) as f:
            sources_config = yaml.safe_load(f)

        total_chunks = 0
        sources_processed = 0
        errors = []

        # Process PDF/document sources
        if source_filter in (None, "pdf"):
            for pdf_source in sources_config.get("pdf_sources", []):
                try:
                    name = pdf_source.get("name", "")
                    if "url" in pdf_source:
                        count = self.ingest_pdf_url(
                            url=pdf_source["url"],
                            source_name=name,
                            force=force,
                        )
                    elif "path" in pdf_source:
                        file_path = pdf_source["path"]
                        # Resolve relative paths against config file directory
                        resolved = Path(config_path).parent / file_path
                        if not resolved.exists():
                            # Try relative to project root
                            resolved = Path(file_path)
                        if file_path.endswith(".md"):
                            count = self.ingest_markdown(
                                md_path=str(resolved),
                                source_name=name,
                                force=force,
                            )
                        else:
                            count = self.ingest_pdf(
                                pdf_path=str(resolved),
                                source_name=name,
                                force=force,
                            )
                    else:
                        logger.warning(f"Source '{name}' has no url or path")
                        continue

                    total_chunks += count
                    sources_processed += 1
                except Exception as e:
                    logger.error(f"Error ingesting '{name}': {e}")
                    errors.append({"source": name, "error": str(e)})

        # Process web sources (requires web_crawler)
        if source_filter in (None, "web"):
            for web_source in sources_config.get("web_sources", []):
                try:
                    name = web_source.get("name", web_source.get("url", ""))
                    url = web_source.get("url", "")
                    depth = web_source.get("depth", 3)

                    if not url:
                        logger.warning(f"Web source '{name}' has no url")
                        continue

                    # Web crawling is handled by the web_crawler module
                    # Import here to avoid circular dependency and make it optional
                    try:
                        from .web_crawler import WebCrawler

                        crawler = WebCrawler(max_depth=depth)
                        pages = crawler.crawl(url)

                        for page_url, page_markdown in pages:
                            count = self.ingest_web(
                                url=page_url,
                                markdown_text=page_markdown,
                                source_name=f"{name}: {page_url}",
                                force=force,
                            )
                            total_chunks += count

                        sources_processed += 1
                    except ImportError:
                        logger.warning(
                            "crawl4ai not installed, skipping web sources. "
                            "Install with: pip install crawl4ai beautifulsoup4"
                        )
                        errors.append({
                            "source": name,
                            "error": "crawl4ai not installed",
                        })
                except Exception as e:
                    logger.error(f"Error ingesting web source '{name}': {e}")
                    errors.append({"source": name, "error": str(e)})

        return {
            "total_chunks": total_chunks,
            "sources_processed": sources_processed,
            "errors": errors,
        }
