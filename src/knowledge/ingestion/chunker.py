"""Heading-aware text chunker for Markdown documents.

Splits Markdown text into chunks that respect heading boundaries,
producing chunks of 500-1000 tokens with 100-token overlap.
"""

import hashlib
import logging
import re
import uuid
from typing import Optional

from ..store.models import ChunkMetadata, DocumentChunk

logger = logging.getLogger(__name__)

# Approximate tokens per character (English text)
CHARS_PER_TOKEN = 4


class Chunker:
    """Heading-aware Markdown text chunker."""

    def __init__(
        self,
        chunk_size: int = 800,
        chunk_overlap: int = 100,
        min_chunk_size: int = 100,
    ):
        """Initialize the chunker.

        Args:
            chunk_size: Target chunk size in tokens.
            chunk_overlap: Overlap between consecutive chunks in tokens.
            min_chunk_size: Minimum chunk size in tokens (smaller chunks are merged).
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
        self._heading_pattern = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)

    def chunk_text(
        self,
        text: str,
        source_type: str,
        source_name: str,
        source_path: Optional[str] = None,
    ) -> list[DocumentChunk]:
        """Split text into heading-aware chunks.

        Args:
            text: Markdown text to chunk.
            source_type: 'pdf' or 'web'.
            source_name: Name of the source document.
            source_path: Path or URL of the source.

        Returns:
            List of DocumentChunk objects.
        """
        sections = self._split_by_headings(text)
        chunks = []

        for section in sections:
            heading = section["heading"]
            breadcrumb = section["breadcrumb"]
            content = section["content"]
            page_number = section.get("page_number")

            section_chunks = self._split_section(content)

            for chunk_text in section_chunks:
                if self._token_count(chunk_text) < self.min_chunk_size:
                    continue

                content_hash = hashlib.sha256(chunk_text.encode()).hexdigest()[:16]
                chunk_id = str(uuid.uuid4())[:12]

                metadata = ChunkMetadata(
                    source_type=source_type,
                    source_name=source_name,
                    source_path=source_path,
                    page_number=page_number,
                    section_heading=heading,
                    breadcrumb=breadcrumb,
                    content_hash=content_hash,
                )

                chunks.append(DocumentChunk(
                    chunk_id=chunk_id,
                    text=chunk_text.strip(),
                    metadata=metadata,
                ))

        logger.info(
            f"Chunked {source_name}: {len(chunks)} chunks "
            f"(avg {sum(len(c.text) for c in chunks) // max(len(chunks), 1)} chars)"
        )
        return chunks

    def _split_by_headings(self, text: str) -> list[dict]:
        """Split text into sections based on Markdown headings.

        Returns a list of dicts with 'heading', 'breadcrumb', 'content', and
        optionally 'page_number' keys.
        """
        sections = []
        heading_stack: list[tuple[int, str]] = []
        current_heading = ""
        current_content_lines: list[str] = []
        current_page: Optional[int] = None

        lines = text.split("\n")

        for line in lines:
            heading_match = self._heading_pattern.match(line)

            # Track page numbers from PDF markers (e.g., "-----" or page break patterns)
            page_match = re.match(r"^---\s*Page\s+(\d+)\s*---$", line, re.IGNORECASE)
            if page_match:
                current_page = int(page_match.group(1))
                continue

            if heading_match:
                # Save previous section
                if current_content_lines:
                    content = "\n".join(current_content_lines).strip()
                    if content:
                        breadcrumb = self._build_breadcrumb(heading_stack)
                        sections.append({
                            "heading": current_heading,
                            "breadcrumb": breadcrumb,
                            "content": content,
                            "page_number": current_page,
                        })

                # Update heading stack
                level = len(heading_match.group(1))
                heading_text = heading_match.group(2).strip()

                # Pop headings at same or deeper level
                while heading_stack and heading_stack[-1][0] >= level:
                    heading_stack.pop()
                heading_stack.append((level, heading_text))

                current_heading = heading_text
                current_content_lines = [line]
            else:
                current_content_lines.append(line)

        # Save final section
        if current_content_lines:
            content = "\n".join(current_content_lines).strip()
            if content:
                breadcrumb = self._build_breadcrumb(heading_stack)
                sections.append({
                    "heading": current_heading,
                    "breadcrumb": breadcrumb,
                    "content": content,
                    "page_number": current_page,
                })

        # If no headings found, treat entire text as one section
        if not sections and text.strip():
            sections.append({
                "heading": "",
                "breadcrumb": "",
                "content": text.strip(),
                "page_number": None,
            })

        return sections

    def _build_breadcrumb(self, heading_stack: list[tuple[int, str]]) -> str:
        """Build a breadcrumb path from the heading stack."""
        if not heading_stack:
            return ""
        return " > ".join(h[1] for h in heading_stack)

    def _split_section(self, text: str) -> list[str]:
        """Split a section into overlapping chunks of target token size.

        Uses paragraph boundaries when possible, falling back to sentence
        boundaries, then character boundaries.
        """
        tokens_approx = self._token_count(text)

        # If section fits in one chunk, return as-is
        if tokens_approx <= self.chunk_size:
            return [text] if text.strip() else []

        # Split by paragraphs (double newline)
        paragraphs = re.split(r"\n\s*\n", text)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        chunks = []
        current_chunk_parts: list[str] = []
        current_tokens = 0

        for para in paragraphs:
            para_tokens = self._token_count(para)

            # If single paragraph exceeds chunk size, split it further
            if para_tokens > self.chunk_size:
                # Flush current chunk first
                if current_chunk_parts:
                    chunks.append("\n\n".join(current_chunk_parts))
                    # Keep overlap from the end
                    overlap_text = self._get_overlap_text(
                        "\n\n".join(current_chunk_parts)
                    )
                    current_chunk_parts = [overlap_text] if overlap_text else []
                    current_tokens = self._token_count(overlap_text) if overlap_text else 0

                # Split large paragraph by sentences
                sentence_chunks = self._split_by_sentences(para)
                chunks.extend(sentence_chunks)
                current_chunk_parts = []
                current_tokens = 0
                continue

            if current_tokens + para_tokens > self.chunk_size and current_chunk_parts:
                chunks.append("\n\n".join(current_chunk_parts))
                # Keep overlap
                overlap_text = self._get_overlap_text(
                    "\n\n".join(current_chunk_parts)
                )
                current_chunk_parts = [overlap_text] if overlap_text else []
                current_tokens = self._token_count(overlap_text) if overlap_text else 0

            current_chunk_parts.append(para)
            current_tokens += para_tokens

        # Flush remaining
        if current_chunk_parts:
            chunks.append("\n\n".join(current_chunk_parts))

        return chunks

    def _split_by_sentences(self, text: str) -> list[str]:
        """Split text by sentence boundaries when paragraphs are too large."""
        sentences = re.split(r"(?<=[.!?])\s+", text)
        chunks = []
        current_parts: list[str] = []
        current_tokens = 0

        for sentence in sentences:
            sent_tokens = self._token_count(sentence)

            if current_tokens + sent_tokens > self.chunk_size and current_parts:
                chunks.append(" ".join(current_parts))
                # Keep overlap
                overlap_text = self._get_overlap_text(" ".join(current_parts))
                current_parts = [overlap_text] if overlap_text else []
                current_tokens = self._token_count(overlap_text) if overlap_text else 0

            current_parts.append(sentence)
            current_tokens += sent_tokens

        if current_parts:
            chunks.append(" ".join(current_parts))

        return chunks

    def _get_overlap_text(self, text: str) -> str:
        """Get the last N tokens of text for overlap."""
        overlap_chars = self.chunk_overlap * CHARS_PER_TOKEN
        if len(text) <= overlap_chars:
            return text
        return text[-overlap_chars:]

    def _token_count(self, text: str) -> int:
        """Approximate token count from character count."""
        return len(text) // CHARS_PER_TOKEN
