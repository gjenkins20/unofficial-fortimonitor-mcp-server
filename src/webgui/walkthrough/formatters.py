"""Output formatting for walkthroughs.

Converts Walkthrough models to Markdown and HTML with screenshot references.
"""

from ..models import Walkthrough


def format_markdown(walkthrough: Walkthrough, include_screenshots: bool = True) -> str:
    """Format a walkthrough as Markdown.

    Args:
        walkthrough: The walkthrough to format.
        include_screenshots: Whether to include screenshot references.

    Returns:
        Markdown-formatted string.
    """
    lines = []
    lines.append(f"# {walkthrough.title}")
    lines.append("")

    if walkthrough.description:
        lines.append(f"*{walkthrough.description}*")
        lines.append("")

    lines.append(f"**Type:** {walkthrough.walkthrough_type.value}")
    if walkthrough.source_crawl_id:
        lines.append(f"**Source Crawl:** {walkthrough.source_crawl_id}")
    lines.append("")
    lines.append("---")
    lines.append("")

    for step in walkthrough.steps:
        lines.append(f"### Step {step.step_number}")
        lines.append("")
        lines.append(f"{step.instruction}")
        lines.append("")

        if step.page_url:
            lines.append(f"**Page:** {step.page_url}")
        if step.element_ref:
            lines.append(f"**Element:** `{step.element_ref}`")
        if step.note:
            lines.append(f"> {step.note}")
        if include_screenshots and step.screenshot_ref:
            lines.append(f"**Screenshot:** `{step.screenshot_ref}`")

        lines.append("")

    return "\n".join(lines)


def format_html(walkthrough: Walkthrough, include_screenshots: bool = True) -> str:
    """Format a walkthrough as HTML.

    Args:
        walkthrough: The walkthrough to format.
        include_screenshots: Whether to include screenshot references.

    Returns:
        HTML-formatted string.
    """
    parts = []
    parts.append("<!DOCTYPE html>")
    parts.append("<html><head>")
    parts.append(f"<title>{_html_escape(walkthrough.title)}</title>")
    parts.append("<style>")
    parts.append("body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }")
    parts.append(".step { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 8px; }")
    parts.append(".step-num { font-weight: bold; color: #0066cc; }")
    parts.append(".meta { color: #666; font-size: 0.9em; margin-top: 8px; }")
    parts.append(".note { background: #f8f9fa; padding: 8px 12px; border-left: 3px solid #0066cc; margin-top: 8px; }")
    parts.append("</style>")
    parts.append("</head><body>")
    parts.append(f"<h1>{_html_escape(walkthrough.title)}</h1>")

    if walkthrough.description:
        parts.append(f"<p><em>{_html_escape(walkthrough.description)}</em></p>")

    parts.append(f"<p><strong>Type:</strong> {walkthrough.walkthrough_type.value}</p>")

    for step in walkthrough.steps:
        parts.append('<div class="step">')
        parts.append(
            f'<p><span class="step-num">Step {step.step_number}:</span> '
            f"{_html_escape(step.instruction)}</p>"
        )

        meta_parts = []
        if step.page_url:
            meta_parts.append(f"Page: {_html_escape(step.page_url)}")
        if step.element_ref:
            meta_parts.append(f"Element: <code>{_html_escape(step.element_ref)}</code>")
        if meta_parts:
            parts.append(f'<div class="meta">{" | ".join(meta_parts)}</div>')

        if step.note:
            parts.append(f'<div class="note">{_html_escape(step.note)}</div>')

        if include_screenshots and step.screenshot_ref:
            parts.append(
                f'<div class="meta">Screenshot: '
                f"<code>{_html_escape(step.screenshot_ref)}</code></div>"
            )

        parts.append("</div>")

    parts.append("</body></html>")
    return "\n".join(parts)


def _html_escape(text: str) -> str:
    """Escape HTML special characters."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
