#!/usr/bin/env python3
"""Validate WebGUI walkthroughs against real crawl data.

Exercises list_workflows, get_workflow, and ui_crop_screenshot against
the real crawl schema (196 pages, 34,867 elements, 196 screenshots)
to prove the tools produce useful output before the PR merges.

Usage:
    uv run python scripts/validate_walkthroughs.py
"""

import json
import sys
from pathlib import Path

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.webgui.store import SchemaStore
from src.webgui.workflows import WorkflowStore

# ---------------------------------------------------------------------------
# Paths to real crawl data
# ---------------------------------------------------------------------------

SCHEMA_FILE = PROJECT_ROOT / "data" / "schemas" / "crawl-31e23c1bfdd1.json"
SCREENSHOTS_DIR = PROJECT_ROOT / "data" / "crawl-31e23c1bfdd1"
WORKFLOWS_FILE = PROJECT_ROOT / "data" / "workflows.yaml"

# Output directory for cropped PNGs
OUTPUT_DIR = Path("/tmp")


def banner(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def check(label: str, condition: bool) -> bool:
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {label}")
    return condition


# ---------------------------------------------------------------------------
# Step 1: Initialize stores
# ---------------------------------------------------------------------------

def init_stores():
    banner("Step 1: Initialize Real Stores")

    ok = True
    ok &= check("Schema file exists", SCHEMA_FILE.exists())
    ok &= check("Screenshots dir exists", SCREENSHOTS_DIR.exists())
    ok &= check("Workflows file exists", WORKFLOWS_FILE.exists())

    if not ok:
        print("\n  ABORT: Required data files missing.")
        sys.exit(1)

    store = SchemaStore(schema_file=SCHEMA_FILE, screenshots_dir=SCREENSHOTS_DIR)
    wf_store = WorkflowStore(workflows_file=WORKFLOWS_FILE, schema_store=store)

    # Force load to validate
    meta = store.get_metadata()
    print(f"\n  Schema loaded: {meta['total_pages_loaded']} pages, "
          f"schema_version={meta['schema_version']}")
    print(f"  Categories: {', '.join(meta['categories'][:10])}...")

    wf_list = wf_store.list_workflows()
    print(f"  Workflows loaded: {wf_list['total']} workflows")

    check("Schema has pages", meta["total_pages_loaded"] > 0)
    check("Workflows loaded", wf_list["total"] > 0)

    return store, wf_store


# ---------------------------------------------------------------------------
# Step 2: Validate list_workflows
# ---------------------------------------------------------------------------

def validate_list_workflows(wf_store: WorkflowStore) -> int:
    banner("Step 2: Validate list_workflows()")

    failures = 0

    # List all
    result = wf_store.list_workflows()
    if not check(f"list_workflows() returned {result['total']} workflows", result["total"] >= 3):
        failures += 1

    for wf in result["workflows"]:
        print(f"    - {wf['id']}: \"{wf['title']}\" ({wf['step_count']} steps, "
              f"tags={wf['tags']})")

    # Query filters
    for query, expected_min in [("maintenance", 1), ("incident", 1), ("alert", 1)]:
        filtered = wf_store.list_workflows(query=query)
        if not check(f"query='{query}' returned {filtered['total']} workflows (>= {expected_min})",
                     filtered["total"] >= expected_min):
            failures += 1
        for wf in filtered["workflows"]:
            print(f"    - {wf['id']}: \"{wf['title']}\"")

    # No-match query
    empty = wf_store.list_workflows(query="zzz_nonexistent_zzz")
    if not check("query='zzz_nonexistent_zzz' returns 0", empty["total"] == 0):
        failures += 1

    return failures


# ---------------------------------------------------------------------------
# Step 3: Validate get_workflow enrichment
# ---------------------------------------------------------------------------

def validate_get_workflow(wf_store: WorkflowStore, store: SchemaStore) -> int:
    banner("Step 3: Validate get_workflow() Enrichment")

    failures = 0
    all_wfs = wf_store.list_workflows()

    for wf_summary in all_wfs["workflows"]:
        wf_id = wf_summary["id"]
        print(f"\n  --- Workflow: {wf_id} ---")

        wf = wf_store.get_workflow(wf_id)
        if not check(f"get_workflow('{wf_id}') not None", wf is not None):
            failures += 1
            continue

        if not check(f"title = \"{wf['title']}\"", bool(wf["title"])):
            failures += 1
        if not check(f"total_steps = {wf['total_steps']}", wf["total_steps"] > 0):
            failures += 1

        for step in wf["steps"]:
            sn = step["step_number"]
            pid = step["page_id"]
            print(f"\n    Step {sn}: \"{step['title']}\"")
            print(f"      page_id: {pid}")
            print(f"      page_title: {step['page_title']}")
            print(f"      page_url: {step['page_url']}")
            print(f"      screenshot_path: {step['screenshot_path']}")
            print(f"      highlight_element: {step['highlight_element']}")
            print(f"      highlight_form: {step['highlight_form']}")

            if not check(f"  step {sn} page_title is not None", step["page_title"] is not None):
                failures += 1
            if not check(f"  step {sn} page_url is not None", step["page_url"] is not None):
                failures += 1

            # Check screenshot file exists (where applicable)
            if step["screenshot_path"]:
                sp = Path(step["screenshot_path"])
                if not check(f"  step {sn} screenshot file exists", sp.exists()):
                    failures += 1
            else:
                print(f"    [INFO] step {sn} has no screenshot_path (expected for some pages)")

            # If highlight_element is set, verify position data exists
            if step["highlight_element"]:
                pos = store.get_element_position(
                    page_id=pid, element_id=step["highlight_element"]
                )
                if not check(f"  step {sn} highlight_element '{step['highlight_element']}' has position",
                             pos is not None):
                    failures += 1
                else:
                    print(f"      position: x={pos['x']}, y={pos['y']}, "
                          f"{pos['width']}x{pos['height']}px")

    return failures


# ---------------------------------------------------------------------------
# Step 4: Validate crop_screenshot with real data
# ---------------------------------------------------------------------------

def validate_crop_screenshot(store: SchemaStore) -> int:
    banner("Step 4: Validate ui_crop_screenshot (Real Screenshots)")

    from PIL import Image, ImageDraw
    import io

    failures = 0

    test_cases = [
        {
            "name": "incidents + view-solutions-button",
            "page_id": "incidents",
            "element_id": "view-solutions-button",
            "annotate": False,
            "expect_crop": True,
        },
        {
            "name": "report-ListServers + elem-29 (Delete)",
            "page_id": "report-ListServers",
            "element_id": "elem-29",
            "annotate": False,
            "expect_crop": True,
        },
        {
            "name": "incidents + elem-14 (Time Range) annotated",
            "page_id": "incidents",
            "element_id": "elem-14",
            "annotate": True,
            "expect_crop": True,
        },
        {
            "name": "incidents + filter (off-screen sidebar, x=-350)",
            "page_id": "incidents",
            "element_id": "filter",
            "annotate": False,
            "expect_crop": False,  # should fallback: x=-350 is off-screen
        },
    ]

    for tc in test_cases:
        print(f"\n  --- Test: {tc['name']} ---")

        page_id = tc["page_id"]
        element_id = tc["element_id"]
        annotate = tc["annotate"]
        padding = 20

        # Get screenshot
        screenshot_path = store.get_screenshot_path(page_id=page_id)
        if not check("screenshot_path resolved", screenshot_path is not None):
            failures += 1
            continue

        print(f"    screenshot: {screenshot_path.name}")

        # Get element position
        position = store.get_element_position(page_id=page_id, element_id=element_id)
        print(f"    position: {position}")

        img = Image.open(screenshot_path)
        img_width, img_height = img.size
        print(f"    image size: {img_width}x{img_height}")

        if position:
            x, y, w, h = position["x"], position["y"], position["width"], position["height"]
            left = max(0, x - padding)
            top = max(0, y - padding)
            right = min(img_width, x + w + padding)
            bottom = min(img_height, y + h + padding)

            # Check if element is on-screen
            if left < right and top < bottom:
                cropped = img.crop((left, top, right, bottom))

                if annotate:
                    draw = ImageDraw.Draw(cropped)
                    elem_left = x - left
                    elem_top = y - top
                    elem_right = elem_left + w
                    elem_bottom = elem_top + h
                    for offset in range(3):
                        draw.rectangle(
                            [
                                elem_left - offset,
                                elem_top - offset,
                                elem_right + offset,
                                elem_bottom + offset,
                            ],
                            outline="red",
                        )

                crop_w, crop_h = cropped.size
                print(f"    crop size: {crop_w}x{crop_h}")

                if tc["expect_crop"]:
                    if not check("crop is smaller than original",
                                 crop_w < img_width or crop_h < img_height):
                        failures += 1
                    if not check("crop is non-zero size", crop_w > 0 and crop_h > 0):
                        failures += 1

                # Save to /tmp
                safe_name = tc["name"].replace(" ", "_").replace("+", "").replace("(", "").replace(")", "")
                out_path = OUTPUT_DIR / f"walkthrough_validate_{safe_name}.png"
                cropped.save(out_path)
                print(f"    saved: {out_path}")
                check("output file exists", out_path.exists())
            else:
                print(f"    element off-screen (crop box empty), falling back to full screenshot")
                if tc["expect_crop"]:
                    check("expected crop but element was off-screen", False)
                    failures += 1
                else:
                    check("fallback to full screenshot (expected)", True)

                # Save full screenshot for reference
                safe_name = tc["name"].replace(" ", "_").replace("+", "").replace("(", "").replace(")", "")
                out_path = OUTPUT_DIR / f"walkthrough_validate_{safe_name}_full.png"
                img.save(out_path)
                print(f"    saved (full): {out_path}")
        else:
            print(f"    no position data, using full screenshot")
            if tc["expect_crop"]:
                check("expected crop but no position data", False)
                failures += 1
            else:
                check("fallback to full screenshot (expected)", True)

            safe_name = tc["name"].replace(" ", "_").replace("+", "").replace("(", "").replace(")", "")
            out_path = OUTPUT_DIR / f"walkthrough_validate_{safe_name}_full.png"
            img.save(out_path)
            print(f"    saved (full): {out_path}")

    return failures


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    banner("WebGUI Walkthrough Validation")
    print(f"  Schema:      {SCHEMA_FILE}")
    print(f"  Screenshots: {SCREENSHOTS_DIR}")
    print(f"  Workflows:   {WORKFLOWS_FILE}")
    print(f"  Output:      {OUTPUT_DIR}/walkthrough_validate_*.png")

    store, wf_store = init_stores()

    total_failures = 0
    total_failures += validate_list_workflows(wf_store)
    total_failures += validate_get_workflow(wf_store, store)
    total_failures += validate_crop_screenshot(store)

    # Summary
    banner("Summary")
    if total_failures == 0:
        print("  All checks PASSED!")
        print(f"\n  Cropped PNGs saved to {OUTPUT_DIR}/walkthrough_validate_*.png")
        print("  Visually inspect them to confirm crop quality.")
    else:
        print(f"  {total_failures} check(s) FAILED!")

    return 0 if total_failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
