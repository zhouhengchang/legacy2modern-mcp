# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-11-24

### Added
- MCP Server with 5 tools: 4 metered + 1 free discovery tool (`l2m-list-tools`).
- Metered API gateway (FastAPI + SQLite): registration, token issuance, per-call credit deduction, HTTP 402 on insufficient credits.
- Dual transport: stdio (local editors) and Streamable HTTP (remote agents).
- Web console (single-file HTML) for login, refactoring and job history.
- VS Code extension skeleton (TypeScript).
- Python SDK (`legacy2modern`).
- Multi-platform publish kit under `publish/` with per-platform scripts and preflight checks.
- GitHub Actions workflow: npm publish (token/OIDC) + MCP Registry publish; GHCR Docker image publish.
- GitHub Pages product landing page under `docs/`.
- MIT LICENSE.

### Notes
- GitHub full chain (repo, release v1.0.0, Actions) is live.
- GitHub Pages site and GHCR container image are live and publicly reachable.
- npmjs.org / MCP Registry / Cloudflare / VS Code / Docker Hub / PyPI require owner-issued tokens.
