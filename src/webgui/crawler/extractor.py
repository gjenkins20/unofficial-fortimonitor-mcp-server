"""DOM element extraction.

Runs JavaScript in page context to discover all interactive elements,
forms, modals, dropdowns, and navigation structures.
"""

import logging
from typing import Dict, List
from urllib.parse import urljoin, urlparse

from ..models import (
    ElementType,
    LinkType,
    NavNode,
    UIElement,
    UIForm,
    UIFormField,
    UILink,
    UIModal,
    UISection,
)

logger = logging.getLogger(__name__)

# JavaScript to extract all interactive elements from the page
_EXTRACT_ELEMENTS_JS = """
() => {
    const results = [];
    const interactiveSelectors = [
        'button', 'a', 'input', 'select', 'textarea',
        '[role="button"]', '[role="tab"]', '[role="menuitem"]',
        '[role="checkbox"]', '[role="radio"]', '[role="switch"]',
        '[role="slider"]', '[role="combobox"]',
        '[onclick]', '[data-toggle]', '[data-action]',
    ];

    const seen = new Set();
    for (const sel of interactiveSelectors) {
        for (const el of document.querySelectorAll(sel)) {
            const id = el.id || el.getAttribute('data-id') || '';
            const key = `${el.tagName}-${id}-${el.textContent?.trim()?.substring(0, 50)}`;
            if (seen.has(key)) continue;
            seen.add(key);

            const rect = el.getBoundingClientRect();
            results.push({
                tag: el.tagName.toLowerCase(),
                id: id,
                type: el.type || el.getAttribute('role') || el.tagName.toLowerCase(),
                label: (el.textContent?.trim() || el.getAttribute('aria-label') || el.getAttribute('title') || el.placeholder || '').substring(0, 200),
                name: el.name || '',
                href: el.href || '',
                selector: _buildSelector(el),
                placeholder: el.placeholder || '',
                required: el.required || false,
                disabled: el.disabled || false,
                options: el.tagName === 'SELECT' ? Array.from(el.options).map(o => o.text) : [],
                position: rect.width > 0 ? {x: Math.round(rect.x), y: Math.round(rect.y), width: Math.round(rect.width), height: Math.round(rect.height)} : null,
            });
        }
    }
    return results;

    function _buildSelector(el) {
        if (el.id) return '#' + CSS.escape(el.id);
        const tag = el.tagName.toLowerCase();
        if (el.name) return tag + '[name="' + el.name + '"]';
        if (el.className && typeof el.className === 'string') {
            const cls = el.className.trim().split(/\\s+/).slice(0, 2).join('.');
            if (cls) return tag + '.' + cls;
        }
        return tag;
    }
}
"""

# JavaScript to extract forms
_EXTRACT_FORMS_JS = """
() => {
    const forms = [];
    for (const form of document.querySelectorAll('form')) {
        const fields = [];
        for (const input of form.querySelectorAll('input, select, textarea')) {
            if (input.type === 'hidden') continue;
            const label_el = input.id ? document.querySelector('label[for="' + input.id + '"]') : null;
            fields.push({
                tag: input.tagName.toLowerCase(),
                id: input.id || '',
                name: input.name || '',
                type: input.type || input.tagName.toLowerCase(),
                label: (label_el?.textContent?.trim() || input.getAttribute('aria-label') || input.placeholder || input.name || '').substring(0, 200),
                required: input.required || false,
                placeholder: input.placeholder || '',
                options: input.tagName === 'SELECT' ? Array.from(input.options).map(o => o.text) : [],
            });
        }
        const submit = form.querySelector('button[type="submit"], input[type="submit"]');
        forms.push({
            id: form.id || '',
            action: form.action || '',
            method: form.method || 'get',
            fields: fields,
            submit_label: submit ? (submit.textContent?.trim() || submit.value || 'Submit') : '',
        });
    }
    return forms;
}
"""

# JavaScript to find modal-like elements
_EXTRACT_MODALS_JS = """
() => {
    const modals = [];
    const modalSelectors = [
        '[role="dialog"]', '.modal', '[aria-modal="true"]',
        '.dialog', '.popup', '[data-modal]',
    ];
    for (const sel of modalSelectors) {
        for (const el of document.querySelectorAll(sel)) {
            const title_el = el.querySelector('h1, h2, h3, h4, .modal-title, [class*="title"]');
            modals.push({
                id: el.id || '',
                title: title_el?.textContent?.trim() || '',
                visible: el.offsetParent !== null || getComputedStyle(el).display !== 'none',
                selector: el.id ? '#' + CSS.escape(el.id) : sel,
            });
        }
    }
    return modals;
}
"""

# JavaScript to extract links
_EXTRACT_LINKS_JS = """
() => {
    const links = [];
    const seen = new Set();
    for (const a of document.querySelectorAll('a[href]')) {
        const href = a.href;
        if (seen.has(href) || !href || href.startsWith('javascript:')) continue;
        seen.add(href);
        links.push({
            text: (a.textContent?.trim() || a.getAttribute('aria-label') || '').substring(0, 200),
            href: href,
        });
    }
    return links;
}
"""

# JavaScript to extract navigation structure
_EXTRACT_NAV_JS = """
() => {
    const navs = [];
    for (const nav of document.querySelectorAll('nav, [role="navigation"], .sidebar, .nav-menu, .main-nav')) {
        const items = [];
        for (const a of nav.querySelectorAll('a[href]')) {
            items.push({
                label: (a.textContent?.trim() || '').substring(0, 100),
                url: a.href,
            });
        }
        if (items.length > 0) {
            navs.push({items: items});
        }
    }
    return navs;
}
"""

# JavaScript to extract breadcrumbs
_EXTRACT_BREADCRUMBS_JS = """
() => {
    const crumbs = [];
    const breadcrumbEl = document.querySelector('[aria-label="breadcrumb"], .breadcrumb, .breadcrumbs, nav.breadcrumb');
    if (breadcrumbEl) {
        for (const item of breadcrumbEl.querySelectorAll('li, a, span')) {
            const text = item.textContent?.trim();
            if (text && text.length < 100 && !crumbs.includes(text)) {
                crumbs.push(text);
            }
        }
    }
    return crumbs;
}
"""


def _map_element_type(raw_type: str) -> ElementType:
    """Map a raw DOM element type string to our ElementType enum."""
    mapping = {
        "button": ElementType.BUTTON,
        "submit": ElementType.BUTTON,
        "reset": ElementType.BUTTON,
        "text": ElementType.INPUT,
        "email": ElementType.INPUT,
        "number": ElementType.INPUT,
        "tel": ElementType.INPUT,
        "url": ElementType.INPUT,
        "search": ElementType.INPUT,
        "password": ElementType.INPUT,
        "select": ElementType.SELECT,
        "select-one": ElementType.SELECT,
        "select-multiple": ElementType.SELECT,
        "checkbox": ElementType.CHECKBOX,
        "radio": ElementType.RADIO,
        "textarea": ElementType.TEXTAREA,
        "a": ElementType.LINK,
        "tab": ElementType.TAB,
        "menuitem": ElementType.MENU_ITEM,
        "combobox": ElementType.DROPDOWN,
        "switch": ElementType.TOGGLE,
        "slider": ElementType.SLIDER,
        "file": ElementType.FILE_UPLOAD,
    }
    return mapping.get(raw_type.lower(), ElementType.OTHER)


def _classify_link(href: str, base_url: str) -> LinkType:
    """Classify a link as internal navigation, external, or anchor."""
    if href.startswith("#"):
        return LinkType.ANCHOR
    parsed = urlparse(href)
    base_parsed = urlparse(base_url)
    if parsed.netloc and parsed.netloc != base_parsed.netloc:
        return LinkType.EXTERNAL
    return LinkType.NAVIGATION


async def extract_page_elements(page, page_url: str) -> Dict:
    """Extract all interactive elements, forms, modals, and links from a page.

    Args:
        page: Playwright Page instance.
        page_url: Current page URL (for link classification).

    Returns:
        Dict with keys: sections, forms, modals, links, breadcrumbs, nav_items, title
    """
    title = await page.title()

    # Run all extraction scripts
    raw_elements = await page.evaluate(_EXTRACT_ELEMENTS_JS)
    raw_forms = await page.evaluate(_EXTRACT_FORMS_JS)
    raw_modals = await page.evaluate(_EXTRACT_MODALS_JS)
    raw_links = await page.evaluate(_EXTRACT_LINKS_JS)
    raw_breadcrumbs = await page.evaluate(_EXTRACT_BREADCRUMBS_JS)
    raw_navs = await page.evaluate(_EXTRACT_NAV_JS)

    # Convert raw elements to UIElement models
    elements = []
    for i, raw in enumerate(raw_elements):
        elements.append(
            UIElement(
                element_id=raw.get("id") or f"elem-{i}",
                type=_map_element_type(raw.get("type", "other")),
                label=raw.get("label", ""),
                selector=raw.get("selector", ""),
                attributes={
                    k: v
                    for k, v in {
                        "placeholder": raw.get("placeholder"),
                        "required": raw.get("required"),
                        "disabled": raw.get("disabled"),
                        "options": raw.get("options") or None,
                        "name": raw.get("name") or None,
                        "href": raw.get("href") or None,
                    }.items()
                    if v
                },
                position=raw.get("position"),
            )
        )

    # Build a single section with all elements (no heading detection yet)
    sections = []
    if elements:
        sections.append(UISection(heading="Page Elements", elements=elements))

    # Convert forms
    forms = []
    for i, raw_form in enumerate(raw_forms):
        fields = []
        for j, raw_field in enumerate(raw_form.get("fields", [])):
            fields.append(
                UIFormField(
                    field_id=raw_field.get("id") or f"field-{i}-{j}",
                    label=raw_field.get("label", ""),
                    type=_map_element_type(raw_field.get("type", "text")),
                    required=raw_field.get("required", False),
                    placeholder=raw_field.get("placeholder", ""),
                    options=raw_field.get("options", []),
                    selector=f"form#{raw_form.get('id', '')} [name=\"{raw_field.get('name', '')}\"]"
                    if raw_form.get("id") and raw_field.get("name")
                    else "",
                )
            )
        submit_label = raw_form.get("submit_label", "Submit")
        forms.append(
            UIForm(
                form_id=raw_form.get("id") or f"form-{i}",
                title=submit_label,
                fields=fields,
                submit_button=UIElement(
                    element_id=f"submit-{i}",
                    type=ElementType.BUTTON,
                    label=submit_label,
                )
                if submit_label
                else None,
            )
        )

    # Convert modals
    modals = []
    for i, raw_modal in enumerate(raw_modals):
        modals.append(
            UIModal(
                modal_id=raw_modal.get("id") or f"modal-{i}",
                title=raw_modal.get("title", ""),
            )
        )

    # Convert links
    links = []
    for raw_link in raw_links:
        href = raw_link.get("href", "")
        links.append(
            UILink(
                text=raw_link.get("text", ""),
                url=href,
                type=_classify_link(href, page_url),
            )
        )

    # Build nav items
    nav_items = []
    for nav in raw_navs:
        for item in nav.get("items", []):
            nav_items.append({
                "label": item.get("label", ""),
                "url": item.get("url", ""),
            })

    return {
        "title": title,
        "breadcrumbs": raw_breadcrumbs,
        "sections": sections,
        "forms": forms,
        "modals": modals,
        "links": links,
        "nav_items": nav_items,
    }


def build_navigation_tree(all_nav_items: List[Dict], base_url: str) -> NavNode:
    """Build a navigation tree from collected nav items across all pages.

    Args:
        all_nav_items: List of {label, url} dicts from all pages.
        base_url: Base URL for resolving relative URLs.

    Returns:
        Root NavNode with children.
    """
    seen = set()
    children = []
    for item in all_nav_items:
        url = item.get("url", "")
        label = item.get("label", "")
        if url and url not in seen and label:
            seen.add(url)
            children.append(NavNode(label=label, url=url))

    return NavNode(label="Root", url=base_url, children=children)
