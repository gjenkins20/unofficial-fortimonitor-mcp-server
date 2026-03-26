# TODO

Project tasks and planned work for FortiMonitor MCP Server.

---

## v2.0 — Knowledge Layer (Current)

- [x] Set up multi-agent infrastructure (agents/, permissions, .gitignore) <!-- PLANE:PENDING -->
- [x] Create knowledge layer module structure (`src/knowledge/`) <!-- PLANE:PENDING -->
- [x] Implement PDF ingestion pipeline (pdf_parser, chunker, embedder, pipeline) <!-- PLANE:PENDING -->
- [x] Implement vector store (LanceDB abstraction + Pydantic models) <!-- PLANE:PENDING -->
- [x] Implement web crawler (crawl4ai + BeautifulSoup) <!-- PLANE:PENDING -->
- [x] Implement knowledge tools (search, retrieval, management) — 8 tools <!-- PLANE:PENDING -->
- [x] Update config, server.py, and dependencies <!-- PLANE:PENDING -->
- [x] Update Docker and deployment files <!-- PLANE:PENDING -->
- [x] Create knowledge layer tests (44 new tests) <!-- PLANE:PENDING -->
- [x] Run full test suite and verify implementation (209 passed) <!-- PLANE:PENDING -->

- [x] Implement WebGUI static knowledge layer (`src/webgui/`) — 7 tools, 52 tests <!-- PLANE:PENDING -->
  - SchemaStore with lazy JSON loading and in-memory word-level indexes
  - Tools: ui_list_pages, ui_get_page, ui_search, ui_get_screenshot, ui_get_navigation, ui_describe_page, ui_get_form
  - Covers 196 crawled pages, 34,867 elements, 737 forms, 1,366 modals
  - Total tool count: 241 → 248

- [x] Add WebGUI walkthrough tools & screenshot cropping — 3 tools, 40 tests <!-- PLANE:PENDING -->
  - WorkflowStore with YAML-defined step-by-step task guides enriched from SchemaStore
  - Tools: ui_list_walkthroughs, ui_get_walkthrough, ui_crop_screenshot
  - 3 walkthroughs: schedule maintenance, investigate incident, configure alert timelines
  - All steps enriched with real page titles, URLs, screenshots, and highlight_element positions
  - Validated against real crawl data (scripts/validate_walkthroughs.py) — all checks pass
  - Total tool count: 248 → 251, total WebGUI tests: 92

- [x] Extract WebGUI tools into standalone MCP server <!-- PLANE:PENDING -->
  - New `fortimonitor-webgui` entry point (`src/webgui/server.py`) with all 10 WebGUI tools
  - Config via env vars (`WEBGUI_SCHEMA_FILE`, `WEBGUI_SCREENSHOTS_DIR`, `WEBGUI_WORKFLOWS_FILE`)
  - Removed WebGUI imports, registry entry, and config fields from main server
  - Main server: 249 tools (no WebGUI), WebGUI server: 10 tools
  - 7 new smoke tests, 99 total WebGUI tests passing

---

## Go Public — Community Edition Release

- [x] **Rotate FortiMonitor API key** <!-- PLANE:PENDING -->
  - Key `798413e3-ac02-...` was in git history (deleted `debug_api.py`, `verify_server_status.py`)
  - **User must rotate in FortiMonitor dashboard** — consider it compromised

- [x] **Scrub git history of secrets** <!-- PLANE:PENDING -->
  - Used `git-filter-repo` to remove `debug_api.py` and `verify_server_status.py` from all history
  - Force-pushed all branches (`main`, `master`, `v2.0-knowledge-layer`) and tags (`v2.0.0`)
  - Verified: `git log --all -p -S "798413e3"` returns nothing

- [x] **Remove/exclude internal files from tracking** <!-- PLANE:PENDING -->
  - Removed `CLAUDE.md`, `.claude/settings.local.json`, `REMAINING_WORK_INSTRUCTIONS.md` from git tracking
  - Added `.claude/`, `CLAUDE.md`, `data/crawl-*/`, `data/schemas/` to `.gitignore`

- [x] **Rename repo to `unofficial-fortimonitor-mcp-server`** <!-- PLANE:PENDING -->
  - Renamed on GitHub via `gh repo rename`
  - Updated all references in README, docs, Docker configs, pyproject.toml, setup.py
  - Added disclaimer to README

- [x] **Add open-source license** <!-- PLANE:PENDING -->
  - MIT License added as `LICENSE` file

- [x] **Update README for public audience** <!-- PLANE:PENDING -->
  - Added "Unofficial" branding and Fortinet disclaimer
  - Added "About the Developer" section
  - Updated repo path references throughout

- [x] **Make GitHub repo public** <!-- PLANE:PENDING -->
  - Git history scrubbed, internal files removed, repo made public

- [x] **Publish to Docker Hub as community edition** <!-- PLANE:PENDING -->
  - Docker Hub repo: `gjenkins20/unofficial-fortimonitor-mcp` (public)
  - CI/CD pushes to both Docker Hub and GHCR
  - Docker Quickstart and docs updated to use Docker Hub as primary source

---

## Marketing — Launch Content

- [x] **Review Reddit draft posts** <!-- PLANE:PENDING -->
  - `marketing/content/reddit-r-fortinet.md` - r/fortinet launch post
  - `marketing/content/reddit-r-claudeai.md` - r/ClaudeAI launch post
  - Approved 2026-03-05

- [ ] **Submit to MCP directories** <!-- PLANE:FMN-2 -->
  - Entries drafted in `marketing/content/mcp-directory-submissions.md`
  - punkpeye/awesome-mcp-servers: PR #2782 open, blocked on Glama listing
  - MCP.so: submitted, pending review
  - mcpservers.org: ready to submit

- [x] **Follow up on Glama listing** <!-- PLANE:PENDING -->
  - Listed at https://glama.ai/mcp/servers/@gjenkins20/unofficial-forti-monitor-mcp-server
  - PR #2782 updated with Glama link

- [ ] **Post to Fortinet Discord** <!-- PLANE:FMN-6 -->
  - Draft and post to an appropriate sub-channel after the three launch posts (directories, r/fortinet, r/ClaudeAI) are published
- [x] **LinkedIn post published (2026-03-05)** <!-- PLANE:PENDING -->
- [ ] **Draft dev.to article** <!-- PLANE:FMN-3 -->

---

## Up Next — Knowledge Layer Quality (v2.1)

- [ ] **Develop a plan to improve knowledge layer answer quality** <!-- PLANE:FMN-4 -->
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

- [ ] **Cross-product docs** <!-- PLANE:FMN-7 -->
  - Expand to FortiGate, FortiManager, and other integrated Fortinet products

- [ ] **Knowledge graph** <!-- PLANE:FMN-8 -->
  - Entity-relation graphs linking FortiMonitor concepts to documentation for graph-enhanced retrieval

- [ ] **Conversational memory** <!-- PLANE:FMN-9 -->
  - Cache Q&A pairs to improve future responses without re-searching

- [ ] **Multi-version support** <!-- PLANE:FMN-10 -->
  - Query docs for specific versions (e.g., "What changed in 25.3?" vs "How does this work in 26.1?")

- [ ] **Ollama integration** <!-- PLANE:FMN-11 -->
  - Leverage local Ollama setup for higher-quality embeddings and re-ranking

- [ ] **Auto version detection** <!-- PLANE:FMN-12 -->
  - Monitor docs.fortinet.com for new releases and auto-trigger ingestion

---

## Scheduled

- [ ] **Push PyJWT security fix and rebuild Docker image (2026-03-19)** <!-- PLANE:PENDING -->
  - Commit f4c9c7a pins pyjwt>=2.12.0 to fix CVE-2026-32597 (HIGH, CVSS 7.5)
  - Push to origin, rebuild and push Docker image to Docker Hub
  - Re-scan with `docker scout cves` to confirm 0 critical/high in published image

---

## Completed

- [x] P1-P4 API tools implementation (241 tools) <!-- PLANE:PENDING -->
- [x] Docker multi-stage build and CI/CD pipeline <!-- PLANE:PENDING -->
- [x] Documentation (User Guide, Developer Guide, Docker Quickstart) <!-- PLANE:PENDING -->
- [x] Security fixes (CVE-2025-8869, CVE-2026-24049, CVE-2026-23949, CVE-2026-32597) <!-- PLANE:PENDING -->
- [x] WebGUI static knowledge layer — 7 MCP tools (248 total) <!-- PLANE:PENDING -->
- [x] WebGUI walkthrough tools & screenshot cropping — 3 MCP tools (251 total) <!-- PLANE:PENDING -->
- [x] Extract WebGUI into standalone MCP server (249 + 10 tools) <!-- PLANE:PENDING -->

---

*Last updated: 2026-03-13*
