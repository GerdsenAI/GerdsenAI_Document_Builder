# Changelog

All notable changes to the GerdsenAI Document Builder.

---

## [2.1.0] — 2026-02-23

### Added
- **Language-aware code block styling** — diff, treeview, shell, and generic blocks each render with distinct colors and formatting
- **Configurable cover/footer logos** via `config.yaml → logos.cover` / `logos.footer`
- **Interactive logo selector** — `setup.py` option [9] to pick logos from Assets/
- **`.flake8` config** — sets `max-line-length = 120` to suppress harmless line-length warnings
- `_detect_code_language()` method for extracting language from fenced code blocks
- `_render_code_block()` method for per-line styling (diff coloring, tree highlighting, shell prompt detection)
- `code_blocks` configuration section in `config.yaml` with per-type color customization
- `DiffCode`, `TreeCode`, `ShellCode`, `GenericCode` paragraph styles
- `CHANGELOG.md` with full version history

### Changed
- **Consolidated documentation** — merged `MERMAID_SETUP.md` and `VENV_SETUP.md` into `README.MD`
- README now includes cover page customization guide, `logos` config docs, full config reference, and Mermaid docs
- **Comment-preserving config writes** — `setup.py` logo selector uses regex replacement instead of `yaml.dump()` to preserve YAML comments
- **Removed all emojis** from `document_builder_reportlab.py` and `build_document.sh` — replaced with plain-text tags (`[OK]`, `[FAIL]`, `[WARN]`, etc.)
- Fixed bare `except:` → `except Exception:` in footer logo rendering
- Fixed `textwrap` import — moved from inline back to top-level
- Fixed unused variables (`original_code`, `node_counter`, `output`) and f-strings without placeholders
- Bumped version to v2.1.0 in `setup.py` and `build_document.sh`

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
