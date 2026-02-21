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

---

## Up Next — Knowledge Layer Quality (v2.1)

- [ ] **Ingest FortiMonitor community knowledge base articles**
  - Source: https://community.fortinet.com/t5/FortiMonitor/tkb-p/TKB45
  - Crawl and ingest Fortinet community KB articles into the knowledge layer
  - Articles cover real-world troubleshooting, configuration guides, and best practices
  - Add as a web source in `data/sources.yaml`
  - Handle pagination across the KB listing pages
  - Preserve article metadata (title, date, category, URL) for attribution
  - Validate ingested content with sample queries against KB topics

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

## v2.2 — WebGUI Crawler & Walkthrough Generator

- [x] **Phase 1: Foundation** — Pydantic models, schema store, screenshot manager
- [x] **Phase 2: Crawler Engine** — Playwright BFS crawler, authenticator, DOM extractor, state persistence
- [x] **Phase 3: Walkthrough Generator + Schema Differ** — Navigation/task/section/flow walkthroughs, Markdown/HTML formatters, schema version comparison
- [x] **Phase 4: MCP Tools + Server Integration** — 8 new MCP tools (`ui_crawl_start`, `ui_crawl_status`, `ui_schema_list_pages`, `ui_schema_get_page`, `ui_schema_search`, `ui_schema_compare`, `ui_screenshot_get`, `ui_generate_walkthrough`), server.py registry, config settings, optional `playwright` dependency
- [x] **Tests** — 134 new tests (models, schema store, crawler, differ, walkthrough, tools), full suite 343 passed

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

---

*Last updated: 2026-02-21*
