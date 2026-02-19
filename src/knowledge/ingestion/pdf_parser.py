"""PDF-to-Markdown parser using PyMuPDF (pymupdf4llm).

Converts FortiMonitor PDF documentation to structured Markdown text,
preserving headings, tables, and document structure.
"""

import logging
from pathlib import Path
from typing import Optional

import pymupdf4llm

logger = logging.getLogger(__name__)


class PDFParser:
    """Parse PDF files into structured Markdown text."""

    def parse(self, pdf_path: str) -> str:
        """Parse a PDF file and return its content as Markdown.

        Args:
            pdf_path: Path to the PDF file.

        Returns:
            Markdown text with headings, tables, and structure preserved.

        Raises:
            FileNotFoundError: If the PDF file doesn't exist.
            ValueError: If the file is not a valid PDF.
        """
        path = Path(pdf_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        if path.suffix.lower() != ".pdf":
            raise ValueError(f"Not a PDF file: {pdf_path}")

        logger.info(f"Parsing PDF: {path.name}")

        try:
            md_text = pymupdf4llm.to_markdown(str(path))
            logger.info(
                f"Parsed {path.name}: {len(md_text)} chars"
            )
            return md_text
        except Exception as e:
            logger.error(f"Error parsing {path.name}: {e}")
            raise

    def parse_pages(
        self, pdf_path: str, start_page: int = 0, end_page: Optional[int] = None
    ) -> str:
        """Parse specific pages of a PDF.

        Args:
            pdf_path: Path to the PDF file.
            start_page: Starting page (0-indexed).
            end_page: Ending page (exclusive). None for all remaining.

        Returns:
            Markdown text for the specified page range.
        """
        path = Path(pdf_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        logger.info(f"Parsing PDF pages {start_page}-{end_page}: {path.name}")

        pages = list(range(start_page, end_page)) if end_page else None

        try:
            md_text = pymupdf4llm.to_markdown(str(path), pages=pages)
            return md_text
        except Exception as e:
            logger.error(f"Error parsing pages from {path.name}: {e}")
            raise

    def get_page_count(self, pdf_path: str) -> int:
        """Get the number of pages in a PDF.

        Args:
            pdf_path: Path to the PDF file.

        Returns:
            Number of pages.
        """
        import pymupdf

        path = Path(pdf_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        doc = pymupdf.open(str(path))
        count = doc.page_count
        doc.close()
        return count
