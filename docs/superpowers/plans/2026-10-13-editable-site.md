# Editable Site Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans; implement inline in the current session.

**Goal:** Make the existing site easy to edit and publish the verified refactor to Pages.

**Architecture:** JSON content and shared Jinja2 templates generate static HTML. Existing Tilda assets and DOM contracts remain compatible. GitHub Actions builds and validates a separate publish artifact.

**Tech Stack:** Python 3.10+, Beautiful Soup 4, Jinja2 3, Node.js for syntax checks.

**Spec:** `docs/superpowers/specs/2026-10-13-editable-site-design.md`

## Global Constraints
- Preserve `/`, `/fur/`, `/ceramic/`, `/prints/` and the `/sofibirdsofi/` base path.
- Never run `scripts/mirror.py` or restore `#tildacopy`.
- Keep content and templates inside `site/`; publish only generated HTML and assets.
- Validate/render all pages before writing output.

## Review Focus
- Quotes, ampersands and Unicode in plain text/attributes must render safely.
- A single image becoming a multi-image gallery must gain working controls.
- Nested page links and image paths must work under a project Pages URL.
- Invalid/duplicate record IDs and absent images must stop the build.
- A content-only push must be built and checked automatically before publication.

### Task 1: Content and static build
**Files:** `scripts/build.py`, `site/content/*.json`, `site/templates/**/*.html`, `requirements.txt`, `tests/test_build.py`.
**Interfaces:** `render_site(site_root: Path) -> dict[str, str]`; `build_site(site_root: Path, check: bool = False) -> None`.
- [ ] Add failing integration tests for content editing, galleries, escaping, invalid content and deterministic output.
- [ ] Migrate existing content and generate reusable templates, preserving non-catalogue blocks.
- [ ] Implement validated rendering with Jinja2 StrictUndefined and path/link filters.
- [ ] Run tests and compare content/DOM against the original.

### Task 2: Verification and publication pipeline
**Files:** `scripts/verify.py`, `tests/test_verify.py`, `.github/workflows/pages.yml`, `scripts/package.py`.
**Interfaces:** `verify_site(root: Path) -> list[str]`; package outputs only ready pages and assets.
- [ ] Add failing tests for broken anchors, zoom images, duplicate IDs and gallery indices.
- [ ] Strengthen verification and run checks against all four generated pages.
- [ ] Configure Actions to install dependencies, test, build, verify and package before deployment.

### Task 3: Editing guide and release
**Files:** `README.md`, `docs/editing.md`, `AGENTS.md`, `.gitignore`.
- [ ] Document commands and exact recipes for a new product, photograph, price and common contact edit.
- [ ] Check desktop/mobile pages, navigation, sliders and zoom.
- [ ] Inspect final diff and run full tests, build freshness and file verification.
- [ ] Commit, push `origin main`, watch Pages workflow and smoke-test public routes.
