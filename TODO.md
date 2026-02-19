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

*Last updated: 2026-02-19*
