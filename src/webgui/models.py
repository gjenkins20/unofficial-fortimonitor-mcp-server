"""Pydantic models for WebGUI UI schema representation.

Defines the structured format for capturing web application UI state:
pages, elements, forms, modals, navigation trees, and crawl flows.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# =============================================================================
# Enums
# =============================================================================


class ElementType(str, Enum):
    """Types of interactive UI elements."""

    BUTTON = "button"
    INPUT = "input"
    SELECT = "select"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    TEXTAREA = "textarea"
    LINK = "link"
    TABLE = "table"
    TAB = "tab"
    DROPDOWN = "dropdown"
    TOGGLE = "toggle"
    SLIDER = "slider"
    DATE_PICKER = "date_picker"
    FILE_UPLOAD = "file_upload"
    ICON_BUTTON = "icon_button"
    MENU_ITEM = "menu_item"
    OTHER = "other"


class LinkType(str, Enum):
    """Types of links found in the UI."""

    NAVIGATION = "navigation"
    EXTERNAL = "external"
    ANCHOR = "anchor"
    ACTION = "action"


class CrawlStatus(str, Enum):
    """Status of a crawl operation."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WalkthroughType(str, Enum):
    """Types of walkthrough generation."""

    NAVIGATION = "navigation"
    TASK = "task"
    SECTION = "section"
    FLOW = "flow"


class DiffScope(str, Enum):
    """Scope of schema comparison."""

    SUMMARY = "summary"
    PAGES = "pages"
    ELEMENTS = "elements"
    FULL = "full"


# =============================================================================
# UI Element Models
# =============================================================================


class UIElement(BaseModel):
    """A single interactive UI element on a page."""

    element_id: str = Field(description="Unique identifier for this element")
    type: ElementType = Field(description="Element type")
    label: str = Field(default="", description="Visible label or text content")
    selector: str = Field(default="", description="CSS selector to locate this element")
    attributes: Dict[str, Any] = Field(
        default_factory=dict,
        description="Element attributes: placeholder, options, validation, required, etc.",
    )
    position: Optional[Dict[str, int]] = Field(
        default=None,
        description="Bounding box position: {x, y, width, height}",
    )
    children: List["UIElement"] = Field(
        default_factory=list,
        description="Nested child elements",
    )


class UIFormField(BaseModel):
    """A field within a form."""

    field_id: str = Field(description="Unique field identifier")
    label: str = Field(default="", description="Field label")
    type: ElementType = Field(description="Field input type")
    required: bool = Field(default=False, description="Whether the field is required")
    placeholder: str = Field(default="", description="Placeholder text")
    options: List[str] = Field(
        default_factory=list,
        description="Available options for select/radio/checkbox fields",
    )
    validation: Optional[str] = Field(
        default=None, description="Validation rules or pattern"
    )
    selector: str = Field(default="", description="CSS selector for this field")


class UIForm(BaseModel):
    """A form on a page."""

    form_id: str = Field(description="Unique form identifier")
    title: str = Field(default="", description="Form title or heading")
    fields: List[UIFormField] = Field(
        default_factory=list, description="Form fields"
    )
    submit_button: Optional[UIElement] = Field(
        default=None, description="The submit button element"
    )
    selector: str = Field(default="", description="CSS selector for the form")


class UIModal(BaseModel):
    """A modal dialog on a page."""

    modal_id: str = Field(description="Unique modal identifier")
    title: str = Field(default="", description="Modal title")
    trigger_element: Optional[str] = Field(
        default=None, description="Element ID that triggers this modal"
    )
    elements: List[UIElement] = Field(
        default_factory=list, description="Interactive elements within the modal"
    )
    forms: List[UIForm] = Field(
        default_factory=list, description="Forms within the modal"
    )
    screenshot_path: Optional[str] = Field(
        default=None, description="Path to modal screenshot"
    )


class UISection(BaseModel):
    """A logical section of a page."""

    heading: str = Field(default="", description="Section heading text")
    elements: List[UIElement] = Field(
        default_factory=list, description="Elements in this section"
    )


class UILink(BaseModel):
    """A link found on a page."""

    text: str = Field(default="", description="Link text")
    url: str = Field(description="Link URL")
    type: LinkType = Field(default=LinkType.NAVIGATION, description="Link type")


# =============================================================================
# Page and Navigation Models
# =============================================================================


class UIPage(BaseModel):
    """Complete schema for a single page in the web application."""

    page_id: str = Field(description="Unique page identifier")
    url: str = Field(description="Page URL")
    title: str = Field(default="", description="Page title")
    breadcrumbs: List[str] = Field(
        default_factory=list, description="Breadcrumb navigation path"
    )
    screenshot_path: Optional[str] = Field(
        default=None, description="Path to full-page screenshot"
    )
    sections: List[UISection] = Field(
        default_factory=list, description="Page sections"
    )
    modals: List[UIModal] = Field(
        default_factory=list, description="Modals accessible from this page"
    )
    forms: List[UIForm] = Field(
        default_factory=list, description="Forms on this page"
    )
    links: List[UILink] = Field(
        default_factory=list, description="Links on this page"
    )

    @property
    def element_count(self) -> int:
        """Total count of interactive elements on this page."""
        count = sum(len(s.elements) for s in self.sections)
        count += sum(len(m.elements) for m in self.modals)
        count += sum(len(f.fields) for f in self.forms)
        return count


class NavNode(BaseModel):
    """A node in the navigation tree."""

    label: str = Field(description="Navigation item label")
    url: Optional[str] = Field(default=None, description="URL this nav item points to")
    page_id: Optional[str] = Field(
        default=None, description="Associated page ID"
    )
    children: List["NavNode"] = Field(
        default_factory=list, description="Child navigation nodes"
    )


# =============================================================================
# Flow Models
# =============================================================================


class FlowStep(BaseModel):
    """A single step in a UI flow."""

    step_number: int = Field(description="Step sequence number")
    page_url: str = Field(description="URL of the page for this step")
    action: str = Field(description="Action to perform: click, fill, select, navigate")
    target: str = Field(
        default="", description="Target element selector or description"
    )
    description: str = Field(description="Human-readable step description")
    screenshot_path: Optional[str] = Field(
        default=None, description="Screenshot for this step"
    )


class UIFlow(BaseModel):
    """A recorded or generated user flow through the application."""

    flow_id: str = Field(description="Unique flow identifier")
    name: str = Field(description="Flow name/description")
    steps: List[FlowStep] = Field(default_factory=list, description="Flow steps")


# =============================================================================
# Crawl Metadata and Progress
# =============================================================================


class CrawlMetadata(BaseModel):
    """Metadata about a crawl operation."""

    crawl_id: str = Field(description="Unique crawl identifier")
    target_url: str = Field(description="Base URL that was crawled")
    application_name: str = Field(
        default="", description="Name of the application"
    )
    started_at: Optional[datetime] = Field(
        default=None, description="Crawl start time"
    )
    completed_at: Optional[datetime] = Field(
        default=None, description="Crawl completion time"
    )
    total_pages: int = Field(default=0, description="Total pages discovered")
    total_elements: int = Field(default=0, description="Total elements found")
    total_forms: int = Field(default=0, description="Total forms found")
    total_modals: int = Field(default=0, description="Total modals found")


class CrawlProgress(BaseModel):
    """Current progress of a running crawl."""

    crawl_id: str = Field(description="Crawl identifier")
    status: CrawlStatus = Field(
        default=CrawlStatus.PENDING, description="Current crawl status"
    )
    pages_discovered: int = Field(default=0, description="Pages found so far")
    pages_crawled: int = Field(default=0, description="Pages fully crawled")
    pages_remaining: int = Field(default=0, description="Pages left to crawl")
    current_page: Optional[str] = Field(
        default=None, description="URL currently being crawled"
    )
    errors: List[str] = Field(
        default_factory=list, description="Errors encountered during crawl"
    )
    started_at: Optional[datetime] = Field(default=None)
    updated_at: Optional[datetime] = Field(default=None)


# =============================================================================
# Top-Level Schema
# =============================================================================


class UISchema(BaseModel):
    """Complete UI schema for a web application, produced by a single crawl."""

    schema_version: str = Field(default="1.0.0", description="Schema format version")
    crawl_metadata: CrawlMetadata = Field(description="Crawl operation metadata")
    navigation_tree: Optional[NavNode] = Field(
        default=None, description="Root of the navigation tree"
    )
    pages: Dict[str, UIPage] = Field(
        default_factory=dict,
        description="Map of URL -> UIPage for all discovered pages",
    )
    flows: List[UIFlow] = Field(
        default_factory=list, description="Recorded user flows"
    )


# =============================================================================
# Walkthrough Models
# =============================================================================


class WalkthroughStep(BaseModel):
    """A single step in a generated walkthrough."""

    step_number: int = Field(description="Step sequence number")
    instruction: str = Field(description="What the user should do")
    page_url: Optional[str] = Field(default=None, description="Page URL for this step")
    element_ref: Optional[str] = Field(
        default=None, description="Reference to the target element"
    )
    screenshot_ref: Optional[str] = Field(
        default=None, description="Screenshot reference for this step"
    )
    note: Optional[str] = Field(
        default=None, description="Additional context or tip"
    )


class Walkthrough(BaseModel):
    """A generated step-by-step walkthrough."""

    title: str = Field(description="Walkthrough title")
    walkthrough_type: WalkthroughType = Field(description="Type of walkthrough")
    description: str = Field(default="", description="Brief description")
    steps: List[WalkthroughStep] = Field(
        default_factory=list, description="Ordered walkthrough steps"
    )
    source_crawl_id: Optional[str] = Field(
        default=None, description="Crawl ID this walkthrough is based on"
    )


# =============================================================================
# Diff Models
# =============================================================================


class PageDiff(BaseModel):
    """Diff result for a single page between two schema versions."""

    page_url: str = Field(description="Page URL")
    change_type: str = Field(description="added, removed, or modified")
    details: List[str] = Field(
        default_factory=list, description="List of specific changes"
    )


class SchemaDiff(BaseModel):
    """Result of comparing two schema versions."""

    crawl_id_old: str = Field(description="Older crawl ID")
    crawl_id_new: str = Field(description="Newer crawl ID")
    pages_added: List[str] = Field(default_factory=list)
    pages_removed: List[str] = Field(default_factory=list)
    pages_modified: List[PageDiff] = Field(default_factory=list)
    summary: str = Field(default="", description="Human-readable diff summary")
