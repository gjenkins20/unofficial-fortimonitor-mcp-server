"""Walkthrough builder — generates step-by-step instructions from UI schemas.

Supports four walkthrough types:
- navigation: How to get to a specific page
- task: How to accomplish a specific task (matched by description)
- section: Guide to all elements in a page section
- flow: Playback of a recorded flow
"""

import logging
from typing import List, Optional
from urllib.parse import urlparse

from ..models import (
    UIFlow,
    UIPage,
    UISchema,
    Walkthrough,
    WalkthroughStep,
    WalkthroughType,
)

logger = logging.getLogger(__name__)


def _find_page_by_url(schema: UISchema, target_url: str) -> Optional[UIPage]:
    """Find a page by URL, trying exact match then partial path match."""
    # Exact match
    if target_url in schema.pages:
        return schema.pages[target_url]

    # Partial path match
    target_path = urlparse(target_url).path.rstrip("/")
    for url, page in schema.pages.items():
        page_path = urlparse(url).path.rstrip("/")
        if page_path == target_path:
            return page

    # Substring match on URL
    for url, page in schema.pages.items():
        if target_url in url or url in target_url:
            return page

    return None


def _find_navigation_path(
    schema: UISchema, target_url: str
) -> List[str]:
    """Find a path from the root/home page to the target URL.

    Uses BFS through page links to find the shortest path.
    """
    if not schema.pages:
        return []

    # Build adjacency list from page links
    adjacency = {}
    for url, page in schema.pages.items():
        adjacency[url] = [link.url for link in page.links if link.url in schema.pages]

    # Find a starting page (prefer root-like pages)
    start = None
    for url in schema.pages:
        path = urlparse(url).path.rstrip("/")
        if path in ("", "/", "/home", "/dashboard"):
            start = url
            break
    if start is None:
        start = next(iter(schema.pages))

    # BFS
    from collections import deque

    queue = deque([(start, [start])])
    visited = {start}

    while queue:
        current, path = queue.popleft()
        normalized_current = urlparse(current).path.rstrip("/")
        normalized_target = urlparse(target_url).path.rstrip("/")

        if current == target_url or normalized_current == normalized_target:
            return path

        for neighbor in adjacency.get(current, []):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))

    # No path found — return just the target
    return [target_url]


def _find_flow(schema: UISchema, flow_id: str) -> Optional[UIFlow]:
    """Find a flow by ID."""
    for flow in schema.flows:
        if flow.flow_id == flow_id:
            return flow
    return None


def _match_task_pages(schema: UISchema, task_description: str) -> List[UIPage]:
    """Find pages relevant to a task description by keyword matching."""
    keywords = task_description.lower().split()
    scored_pages = []

    for url, page in schema.pages.items():
        score = 0
        searchable = (
            f"{page.title} {' '.join(page.breadcrumbs)} "
            f"{' '.join(s.heading for s in page.sections)} "
            f"{' '.join(f.title for f in page.forms)} "
            f"{' '.join(e.label for s in page.sections for e in s.elements)}"
        ).lower()

        for kw in keywords:
            if kw in searchable:
                score += 1
        if score > 0:
            scored_pages.append((score, page))

    scored_pages.sort(key=lambda x: x[0], reverse=True)
    return [page for _, page in scored_pages[:5]]


def generate_navigation_walkthrough(
    schema: UISchema, target_url: str
) -> Walkthrough:
    """Generate a walkthrough for navigating to a specific page.

    Args:
        schema: The UI schema to generate from.
        target_url: URL of the destination page.

    Returns:
        Walkthrough with navigation steps.
    """
    page = _find_page_by_url(schema, target_url)
    path = _find_navigation_path(schema, target_url)

    steps = []
    for i, url in enumerate(path):
        p = schema.pages.get(url)
        title = p.title if p else url
        if i == 0:
            instruction = f"Start at the '{title}' page ({url})"
        else:
            # Find the link from previous page
            prev_page = schema.pages.get(path[i - 1])
            link_text = ""
            if prev_page:
                for link in prev_page.links:
                    if link.url == url:
                        link_text = link.text
                        break
            if link_text:
                instruction = f"Click '{link_text}' to navigate to '{title}'"
            else:
                instruction = f"Navigate to '{title}' ({url})"

        steps.append(
            WalkthroughStep(
                step_number=i + 1,
                instruction=instruction,
                page_url=url,
                screenshot_ref=p.screenshot_path if p else None,
            )
        )

    dest_title = page.title if page else target_url
    return Walkthrough(
        title=f"Navigate to {dest_title}",
        walkthrough_type=WalkthroughType.NAVIGATION,
        description=f"How to navigate to the {dest_title} page",
        steps=steps,
        source_crawl_id=schema.crawl_metadata.crawl_id,
    )


def generate_task_walkthrough(
    schema: UISchema, task_description: str
) -> Walkthrough:
    """Generate a walkthrough for accomplishing a task.

    Args:
        schema: The UI schema to generate from.
        task_description: Description of what the user wants to do.

    Returns:
        Walkthrough with task steps.
    """
    relevant_pages = _match_task_pages(schema, task_description)

    steps = []
    step_num = 1

    for page in relevant_pages:
        # Add navigation step
        steps.append(
            WalkthroughStep(
                step_number=step_num,
                instruction=f"Go to the '{page.title}' page ({page.url})",
                page_url=page.url,
                screenshot_ref=page.screenshot_path,
            )
        )
        step_num += 1

        # Add form interaction steps
        for form in page.forms:
            for field in form.fields:
                action = "Select" if field.type.value in ("select", "dropdown") else "Enter"
                required = " (required)" if field.required else ""
                instruction = f"{action} the '{field.label}' field{required}"
                if field.options:
                    instruction += f" — options: {', '.join(field.options[:5])}"
                steps.append(
                    WalkthroughStep(
                        step_number=step_num,
                        instruction=instruction,
                        page_url=page.url,
                        element_ref=field.field_id,
                    )
                )
                step_num += 1

            if form.submit_button:
                steps.append(
                    WalkthroughStep(
                        step_number=step_num,
                        instruction=f"Click '{form.submit_button.label}' to submit",
                        page_url=page.url,
                        element_ref=form.submit_button.element_id,
                    )
                )
                step_num += 1

    if not steps:
        steps.append(
            WalkthroughStep(
                step_number=1,
                instruction=f"No matching pages found for: {task_description}",
            )
        )

    return Walkthrough(
        title=f"How to: {task_description}",
        walkthrough_type=WalkthroughType.TASK,
        description=f"Steps to {task_description}",
        steps=steps,
        source_crawl_id=schema.crawl_metadata.crawl_id,
    )


def generate_section_walkthrough(
    schema: UISchema, page_url: str
) -> Walkthrough:
    """Generate a guide to all elements in a page.

    Args:
        schema: The UI schema to generate from.
        page_url: URL of the page to document.

    Returns:
        Walkthrough describing all elements on the page.
    """
    page = _find_page_by_url(schema, page_url)
    if not page:
        return Walkthrough(
            title=f"Guide: {page_url}",
            walkthrough_type=WalkthroughType.SECTION,
            description=f"Page not found: {page_url}",
            steps=[
                WalkthroughStep(
                    step_number=1,
                    instruction=f"Page '{page_url}' was not found in the schema.",
                )
            ],
        )

    steps = []
    step_num = 1

    # Document sections
    for section in page.sections:
        if section.heading:
            steps.append(
                WalkthroughStep(
                    step_number=step_num,
                    instruction=f"Section: {section.heading}",
                    page_url=page.url,
                    note=f"Contains {len(section.elements)} interactive element(s)",
                )
            )
            step_num += 1

        for elem in section.elements:
            steps.append(
                WalkthroughStep(
                    step_number=step_num,
                    instruction=f"{elem.type.value.title()}: '{elem.label}'",
                    page_url=page.url,
                    element_ref=elem.element_id,
                )
            )
            step_num += 1

    # Document forms
    for form in page.forms:
        steps.append(
            WalkthroughStep(
                step_number=step_num,
                instruction=f"Form: {form.title} ({len(form.fields)} field(s))",
                page_url=page.url,
                element_ref=form.form_id,
            )
        )
        step_num += 1

    # Document modals
    for modal in page.modals:
        steps.append(
            WalkthroughStep(
                step_number=step_num,
                instruction=f"Modal dialog: '{modal.title}'",
                page_url=page.url,
                element_ref=modal.modal_id,
                note=f"Triggered by: {modal.trigger_element}" if modal.trigger_element else None,
            )
        )
        step_num += 1

    if not steps:
        steps.append(
            WalkthroughStep(
                step_number=1,
                instruction="This page has no interactive elements.",
                page_url=page.url,
            )
        )

    return Walkthrough(
        title=f"Guide: {page.title}",
        walkthrough_type=WalkthroughType.SECTION,
        description=f"Complete guide to all elements on the {page.title} page",
        steps=steps,
        source_crawl_id=schema.crawl_metadata.crawl_id,
    )


def generate_flow_walkthrough(
    schema: UISchema, flow_id: str
) -> Walkthrough:
    """Generate a walkthrough from a recorded flow.

    Args:
        schema: The UI schema containing the flow.
        flow_id: ID of the flow to play back.

    Returns:
        Walkthrough with flow steps.
    """
    flow = _find_flow(schema, flow_id)
    if not flow:
        return Walkthrough(
            title=f"Flow: {flow_id}",
            walkthrough_type=WalkthroughType.FLOW,
            description=f"Flow not found: {flow_id}",
            steps=[
                WalkthroughStep(
                    step_number=1,
                    instruction=f"Flow '{flow_id}' was not found in the schema.",
                )
            ],
        )

    steps = []
    for fs in flow.steps:
        steps.append(
            WalkthroughStep(
                step_number=fs.step_number,
                instruction=fs.description,
                page_url=fs.page_url,
                element_ref=fs.target,
                screenshot_ref=fs.screenshot_path,
            )
        )

    return Walkthrough(
        title=f"Flow: {flow.name}",
        walkthrough_type=WalkthroughType.FLOW,
        description=f"Playback of the '{flow.name}' flow",
        steps=steps,
        source_crawl_id=schema.crawl_metadata.crawl_id,
    )


def generate_walkthrough(
    schema: UISchema,
    target: str,
    walkthrough_type: WalkthroughType,
) -> Walkthrough:
    """Main entry point — dispatch to the appropriate generator.

    Args:
        schema: UI schema to generate from.
        target: Page URL, task description, or flow ID depending on type.
        walkthrough_type: Type of walkthrough to generate.

    Returns:
        Generated Walkthrough.
    """
    if walkthrough_type == WalkthroughType.NAVIGATION:
        return generate_navigation_walkthrough(schema, target)
    elif walkthrough_type == WalkthroughType.TASK:
        return generate_task_walkthrough(schema, target)
    elif walkthrough_type == WalkthroughType.SECTION:
        return generate_section_walkthrough(schema, target)
    elif walkthrough_type == WalkthroughType.FLOW:
        return generate_flow_walkthrough(schema, target)
    else:
        return Walkthrough(
            title="Unknown walkthrough type",
            walkthrough_type=walkthrough_type,
            steps=[
                WalkthroughStep(
                    step_number=1,
                    instruction=f"Unsupported walkthrough type: {walkthrough_type}",
                )
            ],
        )
