# TODO

Project tasks and planned work for FortiMonitor MCP Server.

---

## v2.0 — Knowledge Layer (Current)

- [x] Set up multi-agent infrastructure (agents/, permissions, .gitignore)
- [x] Create knowledge layer module structure (`src/knowledge/`)
- [x] Implement PDF ingestion pipeline (pdf_parser, chunker, embedder, pipeline)
- [x] Implement vector store (LanceDB abstraction + Pydantic models)
- [x] Implement web crawler (crawl4ai + BeautifulSoup)
- [x] Implement knowledge tools (search, retrieval, management) — 8 tools
- [x] Update config, server.py, and dependencies
- [x] Update Docker and deployment files
- [x] Create knowledge layer tests (44 new tests)
- [x] Run full test suite and verify implementation (209 passed)

- [x] Implement WebGUI static knowledge layer (`src/webgui/`) — 7 tools, 52 tests
  - SchemaStore with lazy JSON loading and in-memory word-level indexes
  - Tools: ui_list_pages, ui_get_page, ui_search, ui_get_screenshot, ui_get_navigation, ui_describe_page, ui_get_form
  - Covers 196 crawled pages, 34,867 elements, 737 forms, 1,366 modals
  - Total tool count: 241 → 248

- [x] Add WebGUI walkthrough tools & screenshot cropping — 3 tools, 40 tests
  - WorkflowStore with YAML-defined step-by-step task guides enriched from SchemaStore
  - Tools: ui_list_walkthroughs, ui_get_walkthrough, ui_crop_screenshot
  - 3 walkthroughs: schedule maintenance, investigate incident, configure alert timelines
  - All steps enriched with real page titles, URLs, screenshots, and highlight_element positions
  - Validated against real crawl data (scripts/validate_walkthroughs.py) — all checks pass
  - Total tool count: 248 → 251, total WebGUI tests: 92

- [x] Extract WebGUI tools into standalone MCP server
  - New `fortimonitor-webgui` entry point (`src/webgui/server.py`) with all 10 WebGUI tools
  - Config via env vars (`WEBGUI_SCHEMA_FILE`, `WEBGUI_SCREENSHOTS_DIR`, `WEBGUI_WORKFLOWS_FILE`)
  - Removed WebGUI imports, registry entry, and config fields from main server
  - Main server: 249 tools (no WebGUI), WebGUI server: 10 tools
  - 7 new smoke tests, 99 total WebGUI tests passing

---

## Up Next — Knowledge Layer Quality (v2.1)

- [ ] **Develop a plan to improve knowledge layer answer quality**
  - Current knowledge tools return results, but answers lack the depth and polish expected of a knowledge worker
  - Audit the full retrieval pipeline: chunking strategy, embedding model, search/ranking, and response synthesis
  - Evaluate whether chunk sizes, overlap, and metadata are optimized for FortiMonitor content
  - Assess embedding model quality (sentence-transformers) vs. alternatives (Ollama, API-based)
  - Investigate adding re-ranking (cross-encoder or LLM-based) to improve result relevance
  - Consider prompt engineering or response formatting improvements in tool handlers
  - Benchmark current retrieval quality with sample queries and establish a baseline
  - Produce a concrete implementation plan with prioritized improvements

---

## Future Considerations (v2.x+)

These are planned enhancements beyond the initial v2.0 release, from Section 13 of the Implementation Plan.

- [ ] **Cross-product docs**
  - Expand to FortiGate, FortiManager, and other integrated Fortinet products

- [ ] **Knowledge graph**
  - Entity-relation graphs linking FortiMonitor concepts to documentation for graph-enhanced retrieval

- [ ] **Conversational memory**
  - Cache Q&A pairs to improve future responses without re-searching

- [ ] **Multi-version support**
  - Query docs for specific versions (e.g., "What changed in 25.3?" vs "How does this work in 26.1?")

- [ ] **Ollama integration**
  - Leverage local Ollama setup for higher-quality embeddings and re-ranking

- [ ] **Auto version detection**
  - Monitor docs.fortinet.com for new releases and auto-trigger ingestion

---

## Completed

- [x] P1-P4 API tools implementation (241 tools)
- [x] Docker multi-stage build and CI/CD pipeline
- [x] Documentation (User Guide, Developer Guide, Docker Quickstart)
- [x] Security fixes (CVE-2025-8869, CVE-2026-24049, CVE-2026-23949)
- [x] WebGUI static knowledge layer — 7 MCP tools (248 total)
- [x] WebGUI walkthrough tools & screenshot cropping — 3 MCP tools (251 total)
- [x] Extract WebGUI into standalone MCP server (249 + 10 tools)

---

*Last updated: 2026-02-21*
