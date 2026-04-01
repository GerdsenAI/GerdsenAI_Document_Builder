# Changelog

All notable changes to the GerdsenAI Document Builder.

---

## [3.0.0] — 2026-03-31

### Added
- **Image and screenshot embedding** — markdown `![alt](path)` syntax now embeds images in PDFs with auto-numbered figure captions (e.g., "Figure 1: Architecture diagram"), aspect-ratio-preserving scaling, and multi-path resolution (absolute, relative to source, GERDSENAI_SOURCE_DIR env var, cwd)
- **Horizontal rule rendering** — `---` and `***` in markdown now render as styled horizontal lines in PDFs (previously silently dropped)
- **FigureCaption style** — centered italic gray caption style for auto-numbered figures
- **CondPageBreak for major headings** — h1/h2 headings insert a conditional page break to prevent orphaning at page bottoms
- **Heading-content grouping** — headings are buffered and grouped with their first following paragraph using KeepTogether, preventing orphaned headings
- **ListItem4 and ListItem5 styles** — nested lists now support 5 levels of depth (up from 3)
- **Configurable table settings** — `config.yaml` now has a `tables:` section with `repeat_header`, `min_column_width`, `wide_table_column_threshold`, and `wide_table_font_size`
- **Configurable bullet character** — `advanced.bullet_character` in config.yaml
- **RGBA transparency handling** — PNG images with alpha channels are composited onto white background before embedding
- **SVG/unsupported format detection** — clear error messages for unsupported image formats
- **Image permission validation** — checks read access before attempting to open images
- **xychart-beta diagram safety** — flowchart-specific sanitization rules are skipped for non-flowchart mermaid diagram types (xychart, pie, gantt, gitgraph, timeline, sankey)

### Fixed
- **Mermaid diagrams not rendering** — the Python `codehilite` markdown extension was stripping the `language-mermaid` class from fenced code blocks; added pre-processing to convert mermaid blocks to raw HTML before codehilite runs
- **Table column widths** — replaced naive character-count estimation with `stringWidth()` from ReportLab for actual rendered text measurement; single-word headers now stay on one line
- **HTML injection in image captions** — alt text is now escaped with `html.escape()` before passing to ReportLab Paragraph
- **Mermaid temp file leaks** — PNG files are now tracked for cleanup immediately after rendering, not after insertion
- **Mermaid error messages** — distinguish between mermaid-cli missing, Playwright missing, and Chromium binary missing
- **Mermaid HTML entity encoding** — uses `html.escape()` instead of manual replacement for complete entity coverage
- **page_break_avoid config enforcement** — the `advanced.page_break_avoid` config list is now actually read and enforced
- **Paragraph alignment heuristic** — uses word count (< 20 words) instead of character count (< 150 chars) for short paragraph detection

### Changed
- **Heading processing consolidated** — six repetitive h1-h6 blocks replaced with a single dict-driven block
- **DPI conversion documented** — the 0.75 pixel-to-point multiplier now has an explanatory comment (96 DPI screen to 72 DPI PDF)

---

## [2.1.1] — 2026-02-27

### Fixed
- **Title page heading overflow** — long titles and subtitles now word-wrap correctly within cover page margins
- **Subtitle wrapping on cover page** — subtitles no longer overflow the page width

### Added
- **GitHub Actions release workflow** — automatically creates a versioned release with packaged tarball on every merge to `main`

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
