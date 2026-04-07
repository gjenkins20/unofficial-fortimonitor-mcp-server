# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **MCP Prompts**: 7 pre-built workflow templates (Morning Situation Report, Investigate Outage, Capacity Planning Review, Change Impact Assessment, Weekly Executive Summary, Alert Noise Audit, Monitoring Coverage Check)
- **Composite Operations**: 5 smart tools that chain multiple API calls (`investigate_server`, `compare_servers`, `audit_monitoring_coverage`, `generate_incident_timeline`, `find_flapping_servers`)
- **MCP Resources**: 4 live data feeds (`fortimonitor://outages/active`, `fortimonitor://health/summary`, `fortimonitor://maintenance/upcoming`, `fortimonitor://alerts/recent`)
- **Webhook Receiver**: Embedded HTTP listener for FortiMonitor outbound webhooks with event storage and query tools
- **Versioning**: CHANGELOG.md, `get_server_version` tool, semantic versioning process
- **License Utilization**: Tool for tracking addon usage vs. entitlements

### Security
- Pinned `pyjwt>=2.12.0` to fix CVE-2026-32597 (HIGH, CVSS 7.5)

## [0.1.0] - 2026-02-06

### Added
- **249 MCP tools** covering 100% of the FortiMonitor/Panopta v2 API
  - Servers, outages, metrics, templates, maintenance, server groups
  - Cloud providers, DEM, compound services, dashboards, status pages
  - Contacts, notifications, rotating contacts, network services
  - SNMP, OnSight, fabric connections, countermeasures, thresholds
  - Users, reference data, monitoring nodes, network service types
  - Bulk operations, reporting, agent resources
- **Knowledge Layer**: PDF ingestion, chunking, embeddings, LanceDB vector store, semantic search
- **WebGUI Server**: 10 standalone tools for querying crawled FortiMonitor UI data (pages, forms, screenshots, walkthroughs)
- Docker multi-stage build with CI/CD pipeline (GitHub Actions)
- Multi-arch Docker images (amd64, arm64) on Docker Hub and GHCR
- Documentation: User Guide, Developer Guide, Windows Deployment Guide
- MIT License

[Unreleased]: https://github.com/gjenkins20/unofficial-fortimonitor-mcp-server/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/gjenkins20/unofficial-fortimonitor-mcp-server/releases/tag/v0.1.0
