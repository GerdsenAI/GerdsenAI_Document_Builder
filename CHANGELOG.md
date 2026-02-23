# Changelog

All notable changes to the GerdsenAI Document Builder.

---

## [2.1.0] — 2026-02-23

### Added
- **Language-aware code block styling** — diff, treeview, shell, and generic blocks each render with distinct colors and formatting
- `_detect_code_language()` method for extracting language from fenced code blocks
- `_render_code_block()` method for per-line styling (diff coloring, tree highlighting, shell prompt detection)
- `code_blocks` configuration section in `config.yaml` with per-type color customization
- `DiffCode`, `TreeCode`, `ShellCode`, `GenericCode` paragraph styles

### Changed
- **Consolidated documentation** — merged `MERMAID_SETUP.md` and `VENV_SETUP.md` into `README.MD`
- README now includes cover page customization guide, full config reference, and Mermaid docs
- Cleaned up 23 unused imports in `document_builder_reportlab.py`

### Removed
- `MERMAID_SETUP.md` (content merged into README)
- `VENV_SETUP.md` (content merged into README)
- `.github/copilot-instructions.md` (untracked)
- Unused imports: `os`, `base64`, `subprocess`, `io`, `textwrap`, `Union`, `letter`, `KeepTogether`, `PageTemplate`, `BaseDocTemplate`, `Frame`, `TA_RIGHT`, `pdfmetrics`, `TTFont`, and all `markdown.extensions.*`

---

## [2.0.0] — 2025-10-20

### Added
- **Mermaid diagram rendering** — local rendering via Playwright + Chromium
- Auto-fix for common Mermaid edge cases (long labels, special characters)
- Fallback to code block display when diagram rendering fails
- Simplified diagram retry on render failure
- Mermaid configuration section in `config.yaml` (theme, viewport, sizing)
- `MERMAID_SETUP.md` and `VENV_SETUP.md` setup guides
- `.vscode/` workspace configuration for auto-venv activation

### Changed
- **Table overflow fix** — tables now auto-fit page width with text wrapping
- Updated `requirements.txt` with Mermaid dependencies
- Updated `config.yaml` with Mermaid and advanced settings

---

## [1.1.0] — 2025-08-22

### Fixed
- Case-insensitive markdown extension handling in build-all and single-file paths
- Robust path resolution to prevent double `To_Build/` prefix

### Added
- Comprehensive `README.md` with multi-platform setup instructions
- `LICENSE.txt` (MIT)

---

## [1.0.0] — 2025-08-20

### Added
- Initial release — Markdown/Text to PDF conversion
- Custom cover pages with logo, title, author, date, version
- Auto-generated Table of Contents with page numbers
- Terminal-style code formatting (green on black)
- Smart text justification based on content type
- YAML front matter support for document metadata
- Configurable filename prefix
- Batch document processing (`--all`)
- `build_document.sh` CLI script
- `config.yaml` for all settings
