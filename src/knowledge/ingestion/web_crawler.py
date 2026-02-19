"""Web content crawler using crawl4ai and BeautifulSoup.

Crawls FortiMonitor documentation pages, strips navigation chrome,
and produces clean Markdown for the ingestion pipeline.
"""

import logging
import re
from typing import Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Elements to strip from web pages (navigation, chrome, footers)
STRIP_SELECTORS = [
    "nav",
    "header",
    "footer",
    ".sidebar",
    ".navigation",
    ".breadcrumb",
    ".toc",
    ".table-of-contents",
    "#sidebar",
    "#navigation",
    "#footer",
    "#header",
    ".cookie-banner",
    ".search-bar",
    "script",
    "style",
    "noscript",
]


class WebCrawler:
    """Crawl web documentation and extract clean Markdown content."""

    def __init__(
        self,
        max_depth: int = 3,
        max_pages: int = 200,
        allowed_domains: Optional[list[str]] = None,
        timeout: int = 30,
    ):
        """Initialize the web crawler.

        Args:
            max_depth: Maximum crawl depth from the seed URL.
            max_pages: Maximum number of pages to crawl.
            allowed_domains: List of allowed domains (None for seed domain only).
            timeout: HTTP request timeout in seconds.
        """
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.allowed_domains = allowed_domains
        self.timeout = timeout
        self._visited: set[str] = set()

    def crawl(self, seed_url: str) -> list[tuple[str, str]]:
        """Crawl starting from a seed URL.

        Args:
            seed_url: The URL to start crawling from.

        Returns:
            List of (url, markdown_content) tuples for each crawled page.
        """
        self._visited.clear()
        seed_domain = urlparse(seed_url).netloc

        if self.allowed_domains is None:
            self.allowed_domains = [seed_domain]

        results = []
        queue = [(seed_url, 0)]  # (url, depth)

        while queue and len(results) < self.max_pages:
            url, depth = queue.pop(0)

            if url in self._visited:
                continue
            if depth > self.max_depth:
                continue

            parsed = urlparse(url)
            if parsed.netloc not in self.allowed_domains:
                continue

            self._visited.add(url)

            try:
                page_content, links = self._fetch_page(url)
                if page_content:
                    markdown = self._html_to_markdown(page_content, url)
                    if markdown.strip():
                        results.append((url, markdown))
                        logger.info(
                            f"Crawled ({len(results)}/{self.max_pages}): {url}"
                        )

                # Add discovered links to queue
                if depth < self.max_depth:
                    for link in links:
                        absolute_url = urljoin(url, link)
                        # Normalize URL
                        absolute_url = absolute_url.split("#")[0].rstrip("/")
                        if absolute_url not in self._visited:
                            queue.append((absolute_url, depth + 1))

            except Exception as e:
                logger.warning(f"Error crawling {url}: {e}")

        logger.info(f"Crawl complete: {len(results)} pages from {seed_url}")
        return results

    def _fetch_page(self, url: str) -> tuple[Optional[str], list[str]]:
        """Fetch a single page and extract links.

        Returns:
            Tuple of (html_content, list_of_links).
        """
        try:
            response = requests.get(
                url,
                timeout=self.timeout,
                headers={
                    "User-Agent": "FortiMonitor-MCP-Knowledge-Crawler/2.0"
                },
            )
            response.raise_for_status()

            content_type = response.headers.get("content-type", "")
            if "text/html" not in content_type:
                return None, []

            html = response.text
            soup = BeautifulSoup(html, "html.parser")

            # Extract links
            links = []
            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"]
                if href and not href.startswith(("javascript:", "mailto:", "tel:")):
                    links.append(href)

            return html, links

        except requests.RequestException as e:
            logger.warning(f"Failed to fetch {url}: {e}")
            return None, []

    def _html_to_markdown(self, html: str, url: str) -> str:
        """Convert HTML to clean Markdown, stripping navigation chrome.

        Args:
            html: Raw HTML content.
            url: Source URL (for context in breadcrumb).

        Returns:
            Cleaned Markdown text.
        """
        soup = BeautifulSoup(html, "html.parser")

        # Remove navigation elements
        for selector in STRIP_SELECTORS:
            for element in soup.select(selector):
                element.decompose()

        # Find main content area
        main_content = (
            soup.find("main")
            or soup.find("article")
            or soup.find(attrs={"role": "main"})
            or soup.find("div", class_="content")
            or soup.find("div", id="content")
            or soup.body
        )

        if not main_content:
            return ""

        # Convert to markdown-like text
        lines = []
        for element in main_content.descendants:
            if element.name in ("h1", "h2", "h3", "h4", "h5", "h6"):
                level = int(element.name[1])
                text = element.get_text(strip=True)
                if text:
                    lines.append(f"\n{'#' * level} {text}\n")

            elif element.name == "p":
                text = element.get_text(strip=True)
                if text:
                    lines.append(f"\n{text}\n")

            elif element.name in ("ul", "ol"):
                for li in element.find_all("li", recursive=False):
                    text = li.get_text(strip=True)
                    if text:
                        lines.append(f"- {text}")

            elif element.name == "pre" or element.name == "code":
                text = element.get_text()
                if text and element.parent.name != "pre":
                    lines.append(f"`{text.strip()}`")
                elif text and element.name == "pre":
                    lines.append(f"\n```\n{text}\n```\n")

            elif element.name == "table":
                lines.append(self._table_to_markdown(element))

        markdown = "\n".join(lines)

        # Clean up excessive whitespace
        markdown = re.sub(r"\n{3,}", "\n\n", markdown)
        return markdown.strip()

    def _table_to_markdown(self, table) -> str:
        """Convert an HTML table to Markdown format."""
        rows = table.find_all("tr")
        if not rows:
            return ""

        md_lines = []
        for i, row in enumerate(rows):
            cells = row.find_all(["th", "td"])
            cell_texts = [cell.get_text(strip=True) for cell in cells]
            md_lines.append("| " + " | ".join(cell_texts) + " |")

            # Add separator after header row
            if i == 0:
                md_lines.append("| " + " | ".join("---" for _ in cells) + " |")

        return "\n".join(md_lines)
