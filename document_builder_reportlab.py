#!/usr/bin/env python3
"""
GerdsenAI Document Builder
Converts Markdown/Text to professional PDFs with custom
styling, Table of Contents, and comprehensive logging.
"""

import os
import sys
import argparse
import re
import tempfile
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
import textwrap
import traceback

# Third-party imports
import markdown
from mermaid_cli import render_mermaid_file_sync
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle,
)
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image as RLImage,
)
from reportlab.platypus import (
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
)
from reportlab.platypus.tableofcontents import (
    TableOfContents,
)
from reportlab.lib.enums import (
    TA_CENTER,
    TA_LEFT,
    TA_JUSTIFY,
)
from reportlab.pdfgen import canvas
from PIL import Image
from bs4 import BeautifulSoup, Tag
import yaml


def setup_logging(repo_path: Path) -> logging.Logger:
    """Setup comprehensive logging system."""
    log_dir = repo_path / "Logs"
    log_dir.mkdir(exist_ok=True)

    # Create logger
    logger = logging.getLogger("DocumentBuilder")
    logger.setLevel(logging.DEBUG)

    # Create formatters
    detailed_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_formatter = logging.Formatter("%(levelname)s: %(message)s")

    # File handler with rotation
    log_file = log_dir / f"document_builder_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = RotatingFileHandler(
        log_file, maxBytes=10 * 1024 * 1024, backupCount=5  # 10MB
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)

    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info("=" * 60)
    logger.info("Document Builder Started")
    logger.info(f"Log file: {log_file}")
    logger.info("=" * 60)

    return logger


class NumberedCanvas(canvas.Canvas):
    """Custom canvas that tracks page numbers for TOC."""

    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self.page_num = 0
        self.toc = None
        self.logger = logging.getLogger("DocumentBuilder.Canvas")

    def showPage(self):
        """Called at the end of each page."""
        self.page_num += 1
        self.logger.debug(f"Page {self.page_num} completed")
        canvas.Canvas.showPage(self)


class TOCDocTemplate(SimpleDocTemplate):
    """Custom document template that properly handles TOC notifications."""

    def __init__(self, *args, **kwargs):
        self.toc = kwargs.pop("toc", None)
        self.heading_entries = []  # Store heading info during first pass
        SimpleDocTemplate.__init__(self, *args, **kwargs)
        self.logger = logging.getLogger("DocumentBuilder.DocTemplate")

    def afterFlowable(self, flowable):
        """Called after each flowable is rendered."""
        # Create bookmark if the flowable has a bookmark name
        if hasattr(flowable, "_bookmarkName"):
            bookmark_name = flowable._bookmarkName  # type: ignore[attr-defined]
            # Create a bookmark at the current position in the PDF
            self.canv.bookmarkPage(bookmark_name)
            # Add to outline (PDF bookmarks visible in PDF readers)
            if hasattr(flowable, "__toc_entry__"):
                level, text, _ = flowable.__toc_entry__  # type: ignore[attr-defined]
                self.canv.addOutlineEntry(text, bookmark_name, level=level)
            self.logger.debug(f"Created bookmark: {bookmark_name}")

        # Check if this is a heading with TOC entry
        if hasattr(flowable, "__toc_entry__"):
            level, text, bookmark = flowable.__toc_entry__  # type: ignore[attr-defined]
            # Get current page number from canvas
            if hasattr(self.canv, "page_num"):
                page_num = self.canv.page_num  # type: ignore[attr-defined]
            else:
                page_num = self.page

            self.logger.debug(
                f"TOC Entry detected: Level {level}, Page {page_num}, Text: {text}"
            )

            # Store entry for second pass
            self.heading_entries.append((level, text, page_num, bookmark))

            # Notify the TOC
            if self.toc:
                self.notify("TOCEntry", (level, text, page_num, bookmark))

    def notify(self, kind, stuff):
        """Handle TOC notifications."""
        if kind == "TOCEntry":
            level, text, page_num, bookmark = stuff
            if self.toc and hasattr(self.toc, "addEntry"):
                # Add the entry to TOC with proper page number
                self.toc.addEntry(level, text, page_num, bookmark)
                self.logger.debug(f"Added TOC entry: {text} -> Page {page_num}")


class DocumentBuilder:
    """Main document builder class for converting Markdown/Text to PDF."""

    def __init__(self, repo_path: str):
        """Initialize the document builder with repository path."""
        self.repo_path = Path(repo_path)
        self.to_build_dir = self.repo_path / "To_Build"
        self.assets_dir = self.repo_path / "Assets"
        self.fonts_dir = self.repo_path / "SF Pro"
        self.output_dir = self.repo_path / "PDFs"

        # Setup logging
        self.logger = setup_logging(self.repo_path)
        self.logger.info(f"Initializing DocumentBuilder with repo path: {repo_path}")

        # Ensure output directory exists
        self.output_dir.mkdir(exist_ok=True)
        self.logger.debug(f"Output directory: {self.output_dir}")

        # Track temporary files for cleanup after PDF is built
        self.temp_files = []

        # Load configuration
        self.config = self._load_config()

        # Register fonts
        self._register_fonts()

        # Setup styles
        self.styles = self._setup_styles()

        # Initialize TOC tracking
        self.toc_entries = []
        self.current_toc = None
        self.heading_counter = 0

        self.logger.info("DocumentBuilder initialized successfully")

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from config.yaml or use defaults."""
        config_path = self.repo_path / "config.yaml"
        self.logger.debug(f"Loading config from: {config_path}")

        default_config = {
            "title": "Document",
            "author": "GerdsenAI",
            "company": "GerdsenAI",
            "date": datetime.now().strftime("%B %d, %Y"),
            "version": "1.0.0",
            "confidential": False,
            "watermark": False,
            "page_size": "A4",
            "margins": {"top": 25, "right": 20, "bottom": 25, "left": 20},
            "header_height": 15,
            "footer_height": 15,
            "filename_prefix": "GerdsenAI_",
        }

        if config_path.exists():
            try:
                with open(config_path, "r") as f:
                    yaml_config = yaml.safe_load(f) or {}

                    # Merge 'default' section into top-level config
                    if "default" in yaml_config:
                        default_config.update(yaml_config["default"])

                    # Merge all other top-level sections
                    # (logos, mermaid, code_blocks, colors, page,
                    #  typography, margins, etc.)
                    for key, value in yaml_config.items():
                        if key == "default":
                            continue  # already merged above
                        default_config[key] = value

                self.logger.debug("Config loaded successfully")
            except Exception as e:
                self.logger.warning(f"Could not load config.yaml: {e}")
        else:
            self.logger.debug("Using default configuration")

        return default_config

    def _register_fonts(self):
        """Register fonts with ReportLab."""
        try:
            self.logger.debug("Registering fonts")
            # ReportLab has built-in support for these fonts
            self.logger.info("Using built-in ReportLab fonts for better compatibility")
        except Exception as e:
            self.logger.error(f"Font registration error: {e}")

    def _setup_styles(
        self,
    ) -> Any:  # Return StyleSheet1, but annotated as Any for compatibility
        """Setup paragraph styles for the document."""
        self.logger.debug("Setting up document styles")
        styles = getSampleStyleSheet()

        # Custom styles
        custom_styles = {
            "CustomTitle": ParagraphStyle(
                "CustomTitle",
                parent=styles["Heading1"],
                fontName="Helvetica-Bold",
                fontSize=24,
                textColor=colors.HexColor("#1a1a1a"),
                spaceAfter=30,
                alignment=TA_CENTER,
            ),
            "CustomHeading1": ParagraphStyle(
                "CustomHeading1",
                parent=styles["Heading1"],
                fontName="Helvetica-Bold",
                fontSize=20,
                textColor=colors.HexColor("#1a1a1a"),
                spaceBefore=24,
                spaceAfter=26,
                keepWithNext=1,
                borderColor=colors.HexColor("#e1e4e8"),
                borderWidth=0,
                borderPadding=0,
            ),
            "CustomHeading2": ParagraphStyle(
                "CustomHeading2",
                parent=styles["Heading2"],
                fontName="Helvetica-Bold",
                fontSize=16,
                textColor=colors.HexColor("#2c3e50"),
                spaceBefore=18,
                spaceAfter=21,
                keepWithNext=1,
            ),
            "CustomHeading3": ParagraphStyle(
                "CustomHeading3",
                parent=styles["Heading3"],
                fontName="Helvetica",
                fontSize=14,
                textColor=colors.HexColor("#34495e"),
                spaceBefore=12,
                spaceAfter=15,
                keepWithNext=1,
            ),
            "CustomHeading4": ParagraphStyle(
                "CustomHeading4",
                parent=styles["Heading4"],
                fontName="Helvetica-Bold",
                fontSize=12,
                textColor=colors.HexColor("#34495e"),
                spaceBefore=10,
                spaceAfter=12,
                keepWithNext=1,
            ),
            "CustomHeading5": ParagraphStyle(
                "CustomHeading5",
                parent=styles["Heading5"],
                fontName="Helvetica-Bold",
                fontSize=11,
                textColor=colors.HexColor("#4a6785"),
                spaceBefore=8,
                spaceAfter=8,
                keepWithNext=1,
            ),
            "CustomBody": ParagraphStyle(
                "CustomBody",
                parent=styles["BodyText"],
                fontName="Helvetica",
                fontSize=11,
                textColor=colors.HexColor("#2c3e50"),
                alignment=TA_JUSTIFY,
                spaceBefore=6,
                spaceAfter=6,
                leading=14,
                wordWrap="LTR",
                splitLongWords=1,
                bulletIndent=0,
                leftIndent=0,
                rightIndent=0,
            ),
            "ListItem1": ParagraphStyle(
                "ListItem1",
                parent=styles["BodyText"],
                fontName="Helvetica",
                fontSize=11,
                textColor=colors.HexColor("#2c3e50"),
                spaceBefore=2,
                spaceAfter=2,
                leading=14,
                leftIndent=18,
                bulletIndent=6,
            ),
            "ListItem2": ParagraphStyle(
                "ListItem2",
                parent=styles["BodyText"],
                fontName="Helvetica",
                fontSize=11,
                textColor=colors.HexColor("#2c3e50"),
                spaceBefore=2,
                spaceAfter=2,
                leading=14,
                leftIndent=36,
                bulletIndent=24,
            ),
            "ListItem3": ParagraphStyle(
                "ListItem3",
                parent=styles["BodyText"],
                fontName="Helvetica",
                fontSize=11,
                textColor=colors.HexColor("#2c3e50"),
                spaceBefore=2,
                spaceAfter=2,
                leading=14,
                leftIndent=54,
                bulletIndent=42,
            ),
            "TableCell": ParagraphStyle(
                "TableCell",
                parent=styles["BodyText"],
                fontName="Helvetica",
                fontSize=8.5,
                textColor=colors.HexColor("#2c3e50"),
                alignment=TA_LEFT,
                spaceBefore=0,
                spaceAfter=0,
                leading=11,
                wordWrap="LTR",
                splitLongWords=1,
                leftIndent=0,
                rightIndent=0,
            ),
            "TableCellHeader": ParagraphStyle(
                "TableCellHeader",
                parent=styles["BodyText"],
                fontName="Helvetica-Bold",
                fontSize=8.5,
                textColor=colors.HexColor("#1a1a1a"),
                alignment=TA_LEFT,
                spaceBefore=0,
                spaceAfter=0,
                leading=11,
                wordWrap="LTR",
                splitLongWords=1,
                leftIndent=0,
                rightIndent=0,
            ),
            "CustomCode": ParagraphStyle(
                "CustomCode",
                parent=styles["Code"],
                fontName="Courier",
                fontSize=9,
                textColor=colors.HexColor("#ffffff"),
                backColor=colors.HexColor("#2b2b2b"),
                borderColor=colors.HexColor("#000000"),
                borderWidth=1,
                borderPadding=8,
                leftIndent=0,
                rightIndent=0,
                spaceAfter=12,
                spaceBefore=12,
            ),
            # --- Block-specific code styles ---
            "DiffCode": ParagraphStyle(
                "DiffCode",
                parent=styles["Code"],
                fontName="Courier",
                fontSize=9,
                textColor=colors.HexColor(
                    self.config.get("code_blocks", {})
                    .get("diff", {})
                    .get("context", "#cdd6f4")
                ),
                backColor=colors.HexColor(
                    self.config.get("code_blocks", {})
                    .get("diff", {})
                    .get("background", "#2b2b2b")
                ),
                borderColor=colors.HexColor(
                    self.config.get("code_blocks", {})
                    .get("diff", {})
                    .get("border_color", "#000000")
                ),
                borderWidth=1,
                borderPadding=8,
                leftIndent=0,
                rightIndent=0,
                spaceAfter=12,
                spaceBefore=12,
            ),
            "TreeCode": ParagraphStyle(
                "TreeCode",
                parent=styles["Code"],
                fontName="Courier",
                fontSize=9,
                textColor=colors.HexColor(
                    self.config.get("code_blocks", {})
                    .get("treeview", {})
                    .get("files", "#cdd6f4")
                ),
                backColor=colors.HexColor(
                    self.config.get("code_blocks", {})
                    .get("treeview", {})
                    .get("background", "#1e1e2e")
                ),
                borderColor=colors.HexColor(
                    self.config.get("code_blocks", {})
                    .get("treeview", {})
                    .get("border_color", "#a6e3a1")
                ),
                borderWidth=3,
                borderPadding=8,
                leftIndent=0,
                rightIndent=0,
                spaceAfter=12,
                spaceBefore=12,
            ),
            "ShellCode": ParagraphStyle(
                "ShellCode",
                parent=styles["Code"],
                fontName="Courier",
                fontSize=9,
                textColor=colors.HexColor(
                    self.config.get("code_blocks", {})
                    .get("shell", {})
                    .get("command", "#00ff00")
                ),
                backColor=colors.HexColor(
                    self.config.get("code_blocks", {})
                    .get("shell", {})
                    .get("background", "#2b2b2b")
                ),
                borderColor=colors.HexColor(
                    self.config.get("code_blocks", {})
                    .get("shell", {})
                    .get("border_color", "#000000")
                ),
                borderWidth=1,
                borderPadding=8,
                leftIndent=0,
                rightIndent=0,
                spaceAfter=12,
                spaceBefore=12,
            ),
            "GenericCode": ParagraphStyle(
                "GenericCode",
                parent=styles["Code"],
                fontName="Courier",
                fontSize=9,
                textColor=colors.HexColor(
                    self.config.get("code_blocks", {})
                    .get("generic", {})
                    .get("text", "#ffffff")
                ),
                backColor=colors.HexColor(
                    self.config.get("code_blocks", {})
                    .get("generic", {})
                    .get("background", "#2b2b2b")
                ),
                borderColor=colors.HexColor(
                    self.config.get("code_blocks", {})
                    .get("generic", {})
                    .get("border_color", "#000000")
                ),
                borderWidth=1,
                borderPadding=8,
                leftIndent=0,
                rightIndent=0,
                spaceAfter=12,
                spaceBefore=12,
            ),
            "CustomInlineCode": ParagraphStyle(
                "CustomInlineCode",
                parent=styles["Normal"],
                fontName="Courier-Bold",
                fontSize=10,
                textColor=colors.HexColor("#000000"),
            ),
            "CustomQuote": ParagraphStyle(
                "CustomQuote",
                parent=styles["BodyText"],
                fontName="Helvetica",
                fontSize=11,
                textColor=colors.HexColor("#555555"),
                leftIndent=20,
                rightIndent=20,
                spaceBefore=12,
                spaceAfter=12,
                borderColor=colors.HexColor("#3498db"),
                borderWidth=0,
                borderPadding=12,
                backColor=colors.HexColor("#f8f9fa"),
            ),
            "FigureCaption": ParagraphStyle(
                "FigureCaption",
                parent=styles["BodyText"],
                fontName="Helvetica-Oblique",
                fontSize=9,
                textColor=colors.HexColor("#6b7280"),
                alignment=TA_CENTER,
                spaceBefore=4,
                spaceAfter=12,
                leading=12,
            ),
            "TOCHeading": ParagraphStyle(
                "TOCHeading",
                parent=styles["Heading1"],
                fontName="Helvetica-Bold",
                fontSize=24,
                spaceAfter=20,
                textColor=colors.HexColor("#1a1a1a"),
                alignment=TA_CENTER,
            ),
            "TOCEntry1": ParagraphStyle(
                "TOCEntry1",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=12,
                leftIndent=0,
                rightIndent=30,
                spaceAfter=6,
                textColor=colors.HexColor("#0066cc"),  # Blue for links
            ),
            "TOCEntry2": ParagraphStyle(
                "TOCEntry2",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=11,
                leftIndent=20,
                rightIndent=30,
                spaceAfter=4,
                textColor=colors.HexColor("#0066cc"),  # Blue for links
            ),
            "TOCEntry3": ParagraphStyle(
                "TOCEntry3",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=10,
                leftIndent=40,
                rightIndent=30,
                spaceAfter=3,
                textColor=colors.HexColor("#0066cc"),  # Blue for links
            ),
        }

        # Add custom styles to the style sheet
        for name, style in custom_styles.items():
            styles.add(style)

        self.logger.debug(f"Created {len(custom_styles)} custom styles")
        return styles

    def _create_toc(self):
        """Create a table of contents."""
        self.logger.debug("Creating Table of Contents object")
        toc = TableOfContents()
        toc.levelStyles = [
            self.styles["TOCEntry1"],
            self.styles["TOCEntry2"],
            self.styles["TOCEntry3"],
        ]
        # Configure dots
        toc.dotsMinLevel = 0  # Show dots for all levels

        # The TOC will automatically use bookmarks created by afterFlowable
        # No need to override internal methods
        return toc

    def _extract_metadata(self, content: str) -> Tuple[str, Dict[str, str]]:
        """Extract metadata from markdown front matter if present."""
        self.logger.debug("Extracting metadata from content")
        metadata = self.config.copy()

        # Check for YAML front matter
        if content.startswith("---"):
            try:
                end_index = content.index("---", 3)
                front_matter = content[3:end_index].strip()
                content = content[end_index + 3 :].strip()

                # Parse front matter using yaml.safe_load for proper value handling
                parsed = yaml.safe_load(front_matter)
                if isinstance(parsed, dict):
                    for key, value in parsed.items():
                        k = key.strip().lower() if isinstance(key, str) else str(key)
                        metadata[k] = str(value) if value is not None else ""

                self.logger.debug(f"Extracted metadata: {list(metadata.keys())}")
            except ValueError:
                self.logger.warning("No closing --- found for front matter")

        # Extract title from first H1 if not in metadata
        if metadata.get("title") == "Document":
            title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
            if title_match:
                metadata["title"] = title_match.group(1)
                self.logger.debug(f"Extracted title from H1: {metadata['title']}")

        return content, metadata

    def _create_heading_with_bookmark(
        self, text: str, style: ParagraphStyle, level: int
    ):
        """Create a heading paragraph with TOC bookmark."""
        self.heading_counter += 1
        bookmark_name = f"heading_{self.heading_counter}"

        # Create the paragraph without HTML anchor (we'll use ReportLab bookmarks)
        para = Paragraph(text, style)

        # Add bookmark name for internal PDF navigation (dynamic attributes)
        para._bookmarkName = bookmark_name  # type: ignore[attr-defined]

        # Add TOC entry information (dynamic attributes)
        para.__toc_entry__ = (level, text, bookmark_name)  # type: ignore[attr-defined]

        self.logger.debug(
            f"Created heading: Level {level}, Text: {text}, Bookmark: {bookmark_name}"
        )
        return para

    def _process_list_element(self, element, story, depth=0):
        """Recursively process ul/ol elements with proper nesting indentation."""
        max_depth = 2  # 0, 1, 2 → ListItem1, ListItem2, ListItem3
        style_key = f"ListItem{min(depth, max_depth) + 1}"
        style = self.styles[style_key]

        is_ordered = element.name == "ol"
        for idx, li in enumerate(element.find_all("li", recursive=False), 1):
            bullet = f"{idx}. " if is_ordered else "\u2022 "

            # Get only the direct text of this <li>, not text from nested lists
            text_parts = []
            for child in li.children:
                if isinstance(child, str):
                    text_parts.append(child.strip())
                elif child.name not in ("ul", "ol"):
                    text_parts.append(child.get_text())
            text = bullet + " ".join(t for t in text_parts if t)

            if text.strip() and text.strip() != bullet.strip():
                story.append(Paragraph(text, style))

            # Recurse into nested lists
            for nested in li.find_all(["ul", "ol"], recursive=False):
                self._process_list_element(nested, story, depth + 1)

    def _sanitize_mermaid_diagram(self, mermaid_code: str) -> Tuple[str, List[str]]:
        """
        Sanitize Mermaid diagram code to fix common edge cases.

        Args:
            mermaid_code: Raw Mermaid diagram code

        Returns:
            Tuple of (sanitized_code, list_of_fixes_applied)
        """
        _ = mermaid_code  # preserved for potential future diff
        fixes_applied = []

        # Get configuration
        mermaid_config = self.config.get("mermaid", {})
        max_label_length = mermaid_config.get("max_label_length", 80)

        # Edge Case 0: REMOVE ALL EMOJIS (they break Mermaid parsing!)
        # This is the FIRST thing we do - emojis cause parse errors
        emoji_pattern = re.compile(
            "["
            "\U0001f600-\U0001f64f"  # emoticons
            "\U0001f300-\U0001f5ff"  # symbols & pictographs
            "\U0001f680-\U0001f6ff"  # transport & map symbols
            "\U0001f1e0-\U0001f1ff"  # flags (iOS)
            "\U00002702-\U000027b0"
            "\U000024c2-\U0001f251"
            "\U0001f900-\U0001f9ff"  # supplemental symbols
            "\U0001fa00-\U0001faff"  # more symbols
            "]+",
            flags=re.UNICODE,
        )

        emoji_count = len(emoji_pattern.findall(mermaid_code))
        if emoji_count > 0:
            mermaid_code = emoji_pattern.sub("", mermaid_code)
            fixes_applied.append(f"Removed {emoji_count} emojis (cause parse errors)")
            self.logger.debug(f"Stripped {emoji_count} emojis from Mermaid diagram")

        # Edge Case 1: Multi-line text in node labels WITH quotes (splitLineToFitWidth error)
        # This is the most common issue - replace ALL newlines inside quotes with <br/>
        # This includes newlines after existing <br/> tags
        def replace_multiline_labels_quoted(match):
            label_content = match.group(1)
            if "\n" in label_content:
                # Replace all remaining newlines, even after <br/> tags
                label_content = re.sub(r"\n+", "<br/>", label_content)
                # Clean up any double <br/> tags
                label_content = re.sub(r"(<br/>)+", "<br/>", label_content)
                if "Replaced newlines in labels with <br/> tags" not in fixes_applied:
                    fixes_applied.append("Replaced newlines in labels with <br/> tags")
            return f'["{label_content}"]'

        mermaid_code = re.sub(
            r'\["([^"]*?)"\]',
            replace_multiline_labels_quoted,
            mermaid_code,
            flags=re.DOTALL,
        )

        # Edge Case 2: Multi-line text in node labels WITHOUT quotes
        # Format: A[Text with\nnewlines]
        def replace_multiline_labels_unquoted(match):
            prefix = match.group(1)
            label_content = match.group(2)
            if "\n" in label_content:
                # Replace all newlines
                label_content = re.sub(r"\n+", "<br/>", label_content)
                # Clean up any double <br/> tags
                label_content = re.sub(r"(<br/>)+", "<br/>", label_content)
                if "Replaced newlines in labels with <br/> tags" not in fixes_applied:
                    fixes_applied.append("Replaced newlines in labels with <br/> tags")
            return f'{prefix}["{label_content}"]'

        # Match node definitions like: A[Text] but not A["Text"]
        mermaid_code = re.sub(
            r'(\b[A-Za-z0-9_]+)\[(?!")([^\]]*?)\]',
            replace_multiline_labels_unquoted,
            mermaid_code,
            flags=re.DOTALL,
        )

        # Edge Case 3: Multi-line text in parentheses labels
        def replace_multiline_parens(match):
            label_content = match.group(1)
            if "\n" in label_content:
                # Replace all newlines
                label_content = re.sub(r"\n+", "<br/>", label_content)
                # Clean up any double <br/> tags
                label_content = re.sub(r"(<br/>)+", "<br/>", label_content)
                if "Replaced newlines in labels with <br/> tags" not in fixes_applied:
                    fixes_applied.append("Replaced newlines in labels with <br/> tags")
            return f'("{label_content}")'

        mermaid_code = re.sub(
            r'\("([^"]*?)"\)', replace_multiline_parens, mermaid_code, flags=re.DOTALL
        )

        # Edge Case 4: Edge/Arrow labels (CRITICAL - MOST COMMON ERROR!)
        # The TabX diagrams have INVALID double-arrow syntax like:
        # WRONG:  -->|-->"label"|-->
        # WRONG:  -->|-->label|-->
        # RIGHT:  -->|"label"|

        arrow_token = r"(?:--?>|===?>|\.\.\.>|-\.-?>|-\.->|---)"

        def strip_internal_arrow(match: re.Match) -> str:
            """Remove stray arrows inside edge labels and ensure quoting."""
            label = match.group("label").strip()
            if not (label.startswith('"') and label.endswith('"')):
                label = f'"{label}"'
            if "Fixed triple-arrow edge labels (invalid syntax)" not in fixes_applied:
                fixes_applied.append("Fixed triple-arrow edge labels (invalid syntax)")
            return f"|{label}|"

        # Remove arrows that appear between the pipes of an edge label
        mermaid_code = re.sub(
            rf"\|\s*{arrow_token}\s*(?P<label>\"[^\"]*\"|[^|\"]+?)\|",
            strip_internal_arrow,
            mermaid_code,
            flags=re.DOTALL,
        )

        def strip_trailing_arrow(match: re.Match) -> str:
            """Remove stray arrows appearing immediately after a labelled edge."""
            spacing = match.group("spacing") or " "
            if "Fixed triple-arrow edge labels (invalid syntax)" not in fixes_applied:
                fixes_applied.append("Fixed triple-arrow edge labels (invalid syntax)")
            return f"|{spacing}"

        # Remove arrows that appear immediately after a labelled edge (e.g. |--> Node)
        mermaid_code = re.sub(
            rf"\|\s*{arrow_token}(?P<spacing>\s*)",
            strip_trailing_arrow,
            mermaid_code,
        )

        def fix_all_edge_label_issues(match):
            """Clean up edge labels: remove arrows, ensure quotes."""
            arrow_before = match.group(1)  # Arrow before first pipe
            content = match.group(2)  # Everything between pipes

            # Remove ALL arrows from content (leading/trailing, with/without spaces)
            cleaned = content
            cleaned = re.sub(
                r"^(?:--?>|===?>|\.\.\.>|-\.-?>|-\.->|---)\s*", "", cleaned
            )
            cleaned = re.sub(
                r"\s*(?:--?>|===?>|\.\.\.>|-\.-?>|-\.->|---)$", "", cleaned
            )
            cleaned = cleaned.strip()

            # Ensure content is quoted
            if not (cleaned.startswith('"') and cleaned.endswith('"')):
                cleaned = f'"{cleaned}"'

            result = f"{arrow_before}|{cleaned}|"

            if content != cleaned:  # Only log if we made changes
                if (
                    "Fixed double-arrow edge labels (invalid syntax)"
                    not in fixes_applied
                ):
                    fixes_applied.append(
                        "Fixed double-arrow edge labels (invalid syntax)"
                    )

            return result

        # Match: arrow + pipe + ANY content + pipe
        # The [^|\n]+? will match anything except pipes or newlines
        before_edge_fix = mermaid_code
        mermaid_code = re.sub(
            r"((?:--?>|===?>|\.\.\.>|-\.-?>|-\.->|---))\|([^|\n]+?)\|",
            fix_all_edge_label_issues,
            mermaid_code,
        )
        if (
            before_edge_fix != mermaid_code
            and "Fixed double-arrow edge labels (invalid syntax)" not in fixes_applied
        ):
            fixes_applied.append("Fixed double-arrow edge labels (invalid syntax)")

        def replace_multiline_edge_labels(match):
            arrow_type = match.group(1)
            label_content = match.group(2)
            if "\n" in label_content:
                # Replace all newlines
                label_content = re.sub(r"\n+", "<br/>", label_content)
                # Clean up any double <br/> tags
                label_content = re.sub(r"(<br/>)+", "<br/>", label_content)
                if (
                    "Replaced newlines in edge labels with <br/> tags"
                    not in fixes_applied
                ):
                    fixes_applied.append(
                        "Replaced newlines in edge labels with <br/> tags"
                    )
            return f'{arrow_type}|"{label_content}"|'

        # Match various arrow types with quoted labels
        # Covers: -->|, ---|, ==>|, -.->|, -.-|, etc.
        mermaid_code = re.sub(
            r'((?:--?>|===?>|\.\.\.>|-\.-?>|-\.->|---))\|"([^"]*?)"\|',
            replace_multiline_edge_labels,
            mermaid_code,
            flags=re.DOTALL,
        )

        # Edge Case 5: Subgraph titles
        def replace_multiline_subgraph(match):
            keyword = match.group(1)
            title_content = match.group(2)
            if "\n" in title_content:
                title_content = re.sub(
                    r"\n+", " ", title_content
                )  # Subgraph titles should be single line
                if "Replaced newlines in subgraph titles" not in fixes_applied:
                    fixes_applied.append("Replaced newlines in subgraph titles")
            return f'{keyword} "{title_content}"'

        mermaid_code = re.sub(
            r'\b(subgraph)\s+"([^"]*?)"',
            replace_multiline_subgraph,
            mermaid_code,
            flags=re.DOTALL,
        )

        # Edge Case 6: Very long labels (auto-wrap at word boundaries)
        def handle_long_labels(match):
            label = match.group(1)
            original_length = len(label)  # Store original length before modification

            if len(label) > max_label_length and "<br/>" not in label:
                words = label.split()
                lines = []
                current_line = []
                current_length = 0

                for word in words:
                    if current_length + len(word) + 1 > max_label_length:
                        lines.append(" ".join(current_line))
                        current_line = [word]
                        current_length = len(word)
                    else:
                        current_line.append(word)
                        current_length += len(word) + 1

                if current_line:
                    lines.append(" ".join(current_line))

                label = "<br/>".join(lines)
                fixes_applied.append(
                    f"Wrapped long label ({original_length} chars -> {len(lines)} lines)"
                )

            return f'["{label}"]'

        mermaid_code = re.sub(r'\["([^"]*?)"\]', handle_long_labels, mermaid_code)

        # Edge Case 7: Excessive whitespace
        lines = mermaid_code.split("\n")
        cleaned_lines = []
        for line in lines:
            line = line.rstrip()
            if line or (cleaned_lines and not cleaned_lines[-1]):
                cleaned_lines.append(line)

        if len(cleaned_lines) != len(lines):
            fixes_applied.append("Cleaned excessive whitespace")

        mermaid_code = "\n".join(cleaned_lines)

        # Edge Case 8: Invalid arrow syntax
        # NOTE: Do NOT add --> after | in edge labels (-->|"label"| is correct, NOT -->|"label"|-->)
        arrow_fixes = {
            r"-->\s*\|": ("-->|", "Fixed arrow syntax (space before pipe)"),
            # REMOVED: r"\|(?![-=])": ("|-->", "Fixed incomplete arrow"),  # This breaks edge labels!
        }

        for pattern, (replacement, description) in arrow_fixes.items():
            if re.search(pattern, mermaid_code):
                mermaid_code = re.sub(pattern, replacement, mermaid_code)
                fixes_applied.append(description)

        # Log fixes if any were applied
        if fixes_applied:
            self.logger.info(
                f"Applied {len(set(fixes_applied))} automatic fixes to Mermaid diagram"
            )
            for fix in set(fixes_applied):  # Use set to avoid duplicate messages
                self.logger.debug(f"  - {fix}")
        else:
            self.logger.debug("No sanitization needed for Mermaid diagram")

        # Final check: verify no newlines remain in labels
        if "\n" in mermaid_code:
            # Count and log all remaining newlines
            newline_count = mermaid_code.count("\n")
            self.logger.debug(
                f"Mermaid code has {newline_count} newlines total (including structure)"
            )

            # Check if newlines are inside quoted labels (various formats)
            remaining_in_brackets = re.findall(
                r'\["[^\]]*\n[^\]]*"\]', mermaid_code, re.DOTALL
            )
            remaining_in_parens = re.findall(
                r'\("[^)]*\n[^)]*"\)', mermaid_code, re.DOTALL
            )
            remaining_in_edges = re.findall(
                r'\|"[^"]*\n[^"]*"\|', mermaid_code, re.DOTALL
            )

            if remaining_in_brackets:
                self.logger.warning(
                    f"WARNING: {len(remaining_in_brackets)} bracket labels still contain newlines!"
                )
                self.logger.debug(f"Examples: {remaining_in_brackets[:2]}")
            if remaining_in_parens:
                self.logger.warning(
                    f"WARNING: {len(remaining_in_parens)} paren labels still contain newlines!"
                )
                self.logger.debug(f"Examples: {remaining_in_parens[:2]}")
            if remaining_in_edges:
                self.logger.warning(
                    f"WARNING: {len(remaining_in_edges)} edge labels still contain newlines!"
                )
                self.logger.debug(f"Examples: {remaining_in_edges[:2]}")

        return mermaid_code, fixes_applied

    def _create_simplified_mermaid(self, mermaid_code: str) -> str:
        """
        Create a simplified version of a Mermaid diagram by removing complex labels.
        Keeps the structure but uses generic labels.

        Args:
            mermaid_code: Original Mermaid diagram code

        Returns:
            Simplified Mermaid diagram code
        """
        lines = mermaid_code.split("\n")
        simplified = [lines[0]]  # Keep diagram type declaration

        for line in lines[1:]:
            line = line.strip()
            if not line or line.startswith("%") or line.startswith("//"):
                continue

            # Replace complex labels with simple generic ones
            # Keep the structure but simplify labels
            line = re.sub(r'\["[^"]*"\]', "[Node]", line)
            line = re.sub(r'\("[^"]*"\)', "(Node)", line)
            line = re.sub(r"\{[^}]*\}", "{Node}", line)

            simplified.append(line)

        return "\n".join(simplified)

    def _process_image_element(self, img_tag, parent_element) -> List:
        """Process a markdown image into ReportLab flowables with figure caption."""
        src = img_tag.get("src", "")
        alt = img_tag.get("alt", "")

        if not src:
            self.logger.warning("Image tag with no src attribute, skipping")
            return []

        # Resolve image path — try multiple locations
        img_path = None
        src_path = Path(src)

        # Try as absolute path first
        if src_path.is_absolute() and src_path.exists():
            img_path = src_path

        # Try relative to original source directory (set from env or input)
        if img_path is None:
            source_dir = getattr(self, "_source_dir", None)
            if source_dir:
                candidate = source_dir / src
                if candidate.exists():
                    img_path = candidate

        # Try relative to original markdown via GERDSENAI_SOURCE_DIR env
        if img_path is None:
            env_source = os.environ.get("GERDSENAI_SOURCE_DIR")
            if env_source:
                candidate = Path(env_source) / src
                if candidate.exists():
                    img_path = candidate

        # Try relative to current working directory
        if img_path is None:
            candidate = Path.cwd() / src
            if candidate.exists():
                img_path = candidate

        if img_path is None:
            self.logger.warning(f"Image not found: {src} (searched from {source_dir})")
            return []

        try:
            # Open image with PIL to get dimensions
            with Image.open(str(img_path)) as pil_img:
                img_width, img_height = pil_img.size

            # Calculate available page width
            page_width = A4[0] - (
                self.config["margins"]["left"] * mm
                + self.config["margins"]["right"] * mm
            )
            max_width = page_width * 0.92  # 92% of available width
            max_height = A4[1] * 0.45  # Max 45% of page height

            # Scale image to fit
            aspect_ratio = img_height / img_width
            scaled_width = min(img_width * 0.75, max_width)
            scaled_height = scaled_width * aspect_ratio

            # Constrain height
            if scaled_height > max_height:
                scaled_height = max_height
                scaled_width = scaled_height / aspect_ratio

            # Create ReportLab Image
            rl_image = RLImage(
                str(img_path), width=scaled_width, height=scaled_height
            )

            # Auto-number figure caption
            self.figure_counter += 1
            caption_text = f"Figure {self.figure_counter}"
            if alt:
                caption_text += f": {alt}"

            caption = Paragraph(caption_text, self.styles["FigureCaption"])

            # Wrap in KeepTogether to prevent page break between image and caption
            figure_block = KeepTogether([
                rl_image,
                Spacer(1, 4),
                caption,
                Spacer(1, 8),
            ])

            self.logger.info(
                f"Embedded image: {img_path.name} as Figure {self.figure_counter} "
                f"({scaled_width:.0f}x{scaled_height:.0f})"
            )
            return [figure_block]

        except Exception as e:
            self.logger.error(f"Failed to process image {src}: {e}")
            return []

    def _render_mermaid_diagram(self, mermaid_code: str) -> Optional[str]:
        """
        Render Mermaid diagram to PNG using local Chromium browser via Playwright.
        Now with automatic edge case detection and fixing.

        Args:
            mermaid_code: The Mermaid diagram code to render

        Returns:
            Path to the rendered PNG file, or None if rendering fails
        """
        mmd_path = None
        png_path = None

        try:
            # Get Mermaid configuration
            mermaid_config = self.config.get("mermaid", {})

            # Check if Mermaid rendering is enabled
            if not mermaid_config.get("enabled", True):
                self.logger.info("Mermaid rendering is disabled in config")
                return None

            # Apply automatic fixes if enabled
            if mermaid_config.get("auto_fix_edge_cases", True):
                sanitized_code, fixes_applied = self._sanitize_mermaid_diagram(
                    mermaid_code
                )

                # Show console warnings if fixes were applied and warnings are enabled
                if fixes_applied and mermaid_config.get("show_fix_warnings", True):
                    unique_fixes = list(set(fixes_applied))  # Remove duplicates
                    print(
                        f"\n[WARN] Auto-fixed Mermaid diagram "
                        f"({len(unique_fixes)} fix{'es' if len(unique_fixes) != 1 else ''}):"
                    )
                    for fix in unique_fixes:
                        print(f"   - {fix}")
                    print()

                mermaid_code = sanitized_code

            # Create temp file for Mermaid code
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".mmd", delete=False, encoding="utf-8"
            ) as mmd_file:
                mmd_file.write(mermaid_code)
                mmd_path = mmd_file.name

            png_path = mmd_path.replace(".mmd", ".png")

            self.logger.info(f"Rendering Mermaid diagram to {png_path}")
            self.logger.debug(f"Mermaid code length: {len(mermaid_code)} characters")

            # Show progress indicator
            print("   Rendering diagram...", end="", flush=True)

            # Render using local Chromium via Playwright
            render_mermaid_file_sync(
                input_file=mmd_path,
                output_file=png_path,
                output_format="png",
                background_color=mermaid_config.get("background", "white"),
                viewport={
                    "width": mermaid_config.get("viewport_width", 1200),
                    "height": mermaid_config.get("viewport_height", 800),
                },
                mermaid_config={
                    "theme": mermaid_config.get("theme", "default"),
                    "htmlLabels": True,  # Required for <br/> tag support in labels
                    "flowchart": {"curve": mermaid_config.get("flow_curve", "basis")},
                },
            )

            print(" done", flush=True)

            # Verify the file was created
            if not Path(png_path).exists():
                raise FileNotFoundError(
                    "Mermaid rendering failed - output file not created"
                )

            self.logger.info("Successfully rendered Mermaid diagram")
            return png_path

        except ImportError as e:
            self.logger.error(
                "mermaid-cli not installed. Run: "
                "pip install mermaid-cli && playwright install chromium"
            )
            self.logger.error(f"Error: {e}")
            if mermaid_config.get("fallback_to_code", True):
                return None
            raise

        except Exception as e:
            print(" failed", flush=True)  # Clear progress indicator

            # Extract the actual error message
            error_msg = str(e)
            if "splitLineToFitWidth does not support newlines" in error_msg:
                error_summary = (
                    "Newlines detected in labels (sanitization may have missed some)"
                )
            elif "Error:" in error_msg:
                # Extract just the error type
                error_summary = error_msg.split("Error:")[1].split("\n")[0].strip()[:80]
            else:
                error_summary = error_msg[:80]

            self.logger.warning(f"Failed to render Mermaid diagram: {error_summary}")
            self.logger.debug(f"Full error: {e}")
            self.logger.debug(f"Mermaid code that failed:\n{mermaid_code[:500]}...")

            # Try simplified rendering if enabled
            if mermaid_config.get("fallback_to_simplified", True):
                try:
                    # Check if we should auto-accept simplified rendering
                    # Get values directly from config to ensure we have the latest settings
                    auto_accept = mermaid_config.get("auto_accept_simplified", False)
                    prompt_user = mermaid_config.get("prompt_before_simplified", True)

                    # If prompt is disabled, treat as auto-accept
                    should_render_simplified = auto_accept or not prompt_user

                    # Only prompt user if configured AND not auto-accepting
                    if prompt_user and not auto_accept and should_render_simplified:
                        print(
                            f"\n[FAIL] Mermaid diagram rendering failed: {error_summary}"
                        )
                        print(
                            "   Diagram can be rendered in simplified form"
                            " (structure preserved, labels removed)"
                        )
                        choice = (
                            input("   Render simplified? (y/n/a=always): ")
                            .strip()
                            .lower()
                        )

                        if choice == "a":
                            # User wants all future simplified diagrams without prompting
                            mermaid_config["prompt_before_simplified"] = False
                            mermaid_config["auto_accept_simplified"] = True
                            should_render_simplified = True
                            print(
                                "   Will auto-render all future"
                                " simplified diagrams"
                                " without prompting\n"
                            )
                        elif choice in ["n", "no"]:
                            should_render_simplified = False
                            self.logger.info(
                                "User declined simplified rendering, falling back to code block"
                            )
                        else:
                            should_render_simplified = True
                    else:
                        # Auto-accepting - show informative message
                        print(f"\n[WARN] Diagram rendering failed: {error_summary}")
                        print("   Automatically rendering simplified version...")

                    if not should_render_simplified:
                        if mermaid_config.get("fallback_to_code", True):
                            return None
                        raise

                    # Create simplified version
                    self.logger.info("Attempting simplified diagram rendering...")
                    if not auto_accept:
                        print("   Rendering simplified diagram...", end="", flush=True)

                    simplified_code = self._create_simplified_mermaid(mermaid_code)

                    # Try rendering simplified version
                    simplified_mmd_path = None
                    simplified_png_path = None
                    try:
                        with tempfile.NamedTemporaryFile(
                            mode="w",
                            suffix="_simplified.mmd",
                            delete=False,
                            encoding="utf-8",
                        ) as simplified_mmd:
                            simplified_mmd.write(simplified_code)
                            simplified_mmd_path = simplified_mmd.name

                        simplified_png_path = simplified_mmd_path.replace(
                            ".mmd", ".png"
                        )

                        render_mermaid_file_sync(
                            input_file=simplified_mmd_path,
                            output_file=simplified_png_path,
                            output_format="png",
                            background_color=mermaid_config.get("background", "white"),
                            viewport={
                                "width": mermaid_config.get("viewport_width", 1200),
                                "height": mermaid_config.get("viewport_height", 800),
                            },
                            mermaid_config={
                                "theme": mermaid_config.get("theme", "default"),
                                "htmlLabels": False,
                                "flowchart": {
                                    "curve": mermaid_config.get("flow_curve", "basis")
                                },
                            },
                        )

                        if Path(simplified_png_path).exists():
                            self.logger.info(
                                "Successfully rendered simplified Mermaid diagram"
                            )
                            if not auto_accept:
                                print(" done", flush=True)
                            print("   [OK] Simplified diagram rendered successfully\n")

                            # DON'T delete the PNG - it's needed by ReportLab!
                            # Only clean up the .mmd file
                            if (
                                simplified_mmd_path
                                and Path(simplified_mmd_path).exists()
                            ):
                                try:
                                    Path(simplified_mmd_path).unlink()
                                except Exception:
                                    pass

                            return simplified_png_path

                    except Exception as e3:
                        # Clean up on error
                        if simplified_mmd_path and Path(simplified_mmd_path).exists():
                            try:
                                Path(simplified_mmd_path).unlink()
                            except Exception:
                                pass
                        if simplified_png_path and Path(simplified_png_path).exists():
                            try:
                                Path(simplified_png_path).unlink()
                            except Exception:
                                pass
                        raise e3

                except Exception as e2:
                    error_summary2 = str(e2)[:80]
                    self.logger.error(
                        f"Simplified rendering also failed: {error_summary2}"
                    )
                    print(
                        f"\n   [FAIL] Simplified rendering also failed: {error_summary2}\n"
                    )

            # Final fallback to code block
            if mermaid_config.get("fallback_to_code", True):
                self.logger.info("Falling back to code block display")
                return None
            raise

        finally:
            # Always clean up input file
            if mmd_path and Path(mmd_path).exists():
                try:
                    Path(mmd_path).unlink()
                    self.logger.debug(f"Cleaned up temp file: {mmd_path}")
                except Exception as e:
                    self.logger.warning(f"Failed to cleanup temp file {mmd_path}: {e}")

    def _detect_code_language(self, code_elem) -> Optional[str]:
        """Extract language from code element CSS classes."""
        if not code_elem:
            return None
        classes = code_elem.get("class") or []
        if isinstance(classes, str):
            classes = [classes]
        for cls in classes:
            cls_str = str(cls).lower()
            if cls_str.startswith("language-"):
                return cls_str.replace("language-", "")
            if cls_str.startswith("highlight-"):
                return cls_str.replace("highlight-", "")
        return None

    def _render_code_block(self, lines: List[str], lang: Optional[str]) -> tuple:
        """Render code lines with language-specific styling.

        Returns:
            tuple: (styled_html_content, style_name)
        """
        cb = self.config.get("code_blocks", {})

        if lang == "diff":
            dc = cb.get("diff", {})
            c_add = dc.get("added", "#a6e3a1")
            c_rem = dc.get("removed", "#f38ba8")
            c_hunk = dc.get("hunk_header", "#89b4fa")
            c_ctx = dc.get("context", "#cdd6f4")
            styled = []
            for line in lines:
                escaped = (
                    line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                )
                if line.startswith("+++") or line.startswith("---"):
                    styled.append(f'<font color="{c_hunk}">' f"<b>{escaped}</b></font>")
                elif line.startswith("+"):
                    styled.append(f'<font color="{c_add}">{escaped}</font>')
                elif line.startswith("-"):
                    styled.append(f'<font color="{c_rem}">{escaped}</font>')
                elif line.startswith("@@"):
                    styled.append(f'<font color="{c_hunk}">' f"<i>{escaped}</i></font>")
                else:
                    styled.append(f'<font color="{c_ctx}">{escaped}</font>')
            return "<br/>".join(styled), "DiffCode"

        elif lang in ("tree", "treeview"):
            tc = cb.get("treeview", {})
            c_tree = tc.get("tree_chars", "#89b4fa")
            c_dir = tc.get("directories", "#f9e2af")
            c_file = tc.get("files", "#cdd6f4")
            styled = []
            for line in lines:
                escaped = (
                    line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                )
                # Highlight tree drawing characters
                processed = re.sub(
                    r"([├└│─┬┤┼]+)",
                    lambda m: (f'<font color="{c_tree}">' f"{m.group(1)}</font>"),
                    escaped,
                )
                # Also handle ASCII tree chars
                processed = re.sub(
                    r"(\|--|\\--|/--|\|   )",
                    lambda m: (f'<font color="{c_tree}">' f"{m.group(1)}</font>"),
                    processed,
                )
                # Directories end with /
                if line.rstrip().endswith("/"):
                    styled.append(
                        f'<font color="{c_dir}">' f"<b>{processed}</b></font>"
                    )
                else:
                    styled.append(f'<font color="{c_file}">' f"{processed}</font>")
            return "<br/>".join(styled), "TreeCode"

        elif lang in ("bash", "sh", "zsh", "shell", "console", "terminal"):
            sc = cb.get("shell", {})
            c_prompt = sc.get("prompt", "#a6e3a1")
            c_cmd = sc.get("command", "#00ff00")
            c_out = sc.get("output", "#94e2d5")
            styled = []
            for line in lines:
                escaped = (
                    line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                )
                # Lines starting with $ # or % are prompts
                prompt_match = re.match(r"^(\s*[$#%]\s*)(.*)", escaped)
                if prompt_match:
                    p, cmd = prompt_match.groups()
                    styled.append(
                        f'<font color="{c_prompt}">'
                        f"<b>{p}</b></font>"
                        f'<font color="{c_cmd}">{cmd}</font>'
                    )
                elif line.startswith("#"):
                    # Comment lines
                    styled.append(f'<font color="{c_prompt}">' f"{escaped}</font>")
                else:
                    # Output lines
                    styled.append(f'<font color="{c_out}">' f"{escaped}</font>")
            return "<br/>".join(styled), "ShellCode"

        elif lang and lang not in ("mermaid",):
            # Known language — use generic light style
            gc = cb.get("generic", {})
            c_text = gc.get("text", "#ffffff")
            styled = []
            for line in lines:
                escaped = (
                    line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                )
                styled.append(f'<font color="{c_text}">{escaped}</font>')
            return "<br/>".join(styled), "GenericCode"

        else:
            # No language or unknown — default terminal style
            styled = []
            for line in lines:
                escaped = (
                    line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                )
                styled.append(escaped)
            return "<br/>".join(styled), "CustomCode"

    def _process_markdown_to_story(
        self, content: str, toc: Optional[TableOfContents] = None
    ) -> List:
        """Process markdown content and convert to ReportLab story elements."""
        self.logger.info("Processing markdown content to story elements")

        # Pre-process: convert Mermaid fenced blocks to raw HTML before
        # codehilite strips the language-mermaid class (GitHub issue workaround)
        mermaid_block_pattern = re.compile(
            r'```mermaid\s*\n(.*?)```', re.DOTALL
        )
        mermaid_count = len(mermaid_block_pattern.findall(content))
        if mermaid_count:
            def _mermaid_to_html(m):
                code = m.group(1).strip().replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                return f'\n<pre><code class="language-mermaid">{code}</code></pre>\n'
            content = mermaid_block_pattern.sub(_mermaid_to_html, content)
            self.logger.info(
                f"Pre-processed {mermaid_count} Mermaid diagram(s) to preserve "
                f"language-mermaid class from codehilite interference"
            )

        # Convert markdown to HTML
        md = markdown.Markdown(
            extensions=[
                "tables",
                "fenced_code",
                "footnotes",
                "attr_list",
                "def_list",
                "abbr",
                "toc",
                "nl2br",
                "sane_lists",
                "codehilite",
                "meta",
            ],
            extension_configs={
                "codehilite": {
                    "css_class": "highlight",
                    "linenums": False,
                    "guess_lang": True,
                },
                "fenced_code": {"lang_prefix": "language-"},
                "toc": {"permalink": False, "baselevel": 1},
            },
        )

        html = md.convert(content)
        soup = BeautifulSoup(html, "html.parser")

        story = []

        # Check if document has any headings
        headings = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
        has_headings = bool(headings)
        self.logger.debug(f"Document has {len(headings)} headings")

        # If headings exist and TOC provided, add it
        if has_headings and toc:
            self.logger.info("Adding Table of Contents to document")
            story.append(Paragraph("Table of Contents", self.styles["TOCHeading"]))
            story.append(Spacer(1, 12))
            story.append(toc)
            story.append(PageBreak())

            self._has_toc_section = True
            self._skip_manual_toc = True
        else:
            self._has_toc_section = False
            self._skip_manual_toc = False

        # Process HTML elements
        skip_manual_toc_section = False

        for element in soup.children:
            if isinstance(element, Tag):
                # Check if this is a manual TOC section to skip
                if element.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                    text = element.get_text().lower()
                    # Start skipping if we encounter a "table of contents" heading
                    if "table of contents" in text and self._has_toc_section:
                        skip_manual_toc_section = True
                        continue
                    # Stop skipping once we hit the next major section
                    elif skip_manual_toc_section:
                        skip_manual_toc_section = False
                        # Don't skip this heading - process it normally

                # Skip list items that are part of a manual TOC
                if skip_manual_toc_section and element.name in ["ol", "ul"]:
                    continue

                # Process headings with TOC support
                if element.name == "h1":
                    text = element.get_text()
                    para = self._create_heading_with_bookmark(
                        text, self.styles["CustomHeading1"], 0
                    )
                    story.append(para)

                elif element.name == "h2":
                    text = element.get_text()
                    para = self._create_heading_with_bookmark(
                        text, self.styles["CustomHeading2"], 1
                    )
                    story.append(para)

                elif element.name == "h3":
                    text = element.get_text()
                    para = self._create_heading_with_bookmark(
                        text, self.styles["CustomHeading3"], 2
                    )
                    story.append(para)

                elif element.name == "h4":
                    text = element.get_text()
                    para = self._create_heading_with_bookmark(
                        text, self.styles["CustomHeading4"], 3
                    )
                    story.append(para)

                elif element.name == "h5":
                    text = element.get_text()
                    para = self._create_heading_with_bookmark(
                        text, self.styles["CustomHeading5"], 4
                    )
                    story.append(para)

                elif element.name == "h6":
                    text = element.get_text()
                    para = self._create_heading_with_bookmark(
                        text, self.styles["CustomHeading5"], 5
                    )
                    story.append(para)

                elif element.name == "p":
                    # Handle paragraphs containing images
                    img_tag = element.find("img")
                    if img_tag:
                        img_elements = self._process_image_element(
                            img_tag, element
                        )
                        if img_elements:
                            story.extend(img_elements)
                        continue

                    # Get paragraph text and clean HTML attributes
                    para_text = str(element)

                    # Remove problematic attributes
                    para_text = re.sub(r'\s*id="[^"]*"', "", para_text)
                    para_text = re.sub(r'\s*class="[^"]*"', "", para_text)

                    # Convert footnote references
                    para_text = re.sub(
                        r"<sup[^>]*><a[^>]*>(\d+)</a></sup>",
                        r"<sup>\1</sup>",
                        para_text,
                    )

                    # Check for code elements
                    if element.find("code"):
                        para_parts = []
                        parts = re.split(r"(<code>.*?</code>)", para_text)
                        code_count = 0
                        for part in parts:
                            if part.startswith("<code>") and part.endswith("</code>"):
                                code_count += 1
                                code_content = part[6:-7]
                                para_parts.append(
                                    f'<font name="Courier-Bold" size="10" color="#000000">{code_content}</font>'
                                )
                            elif part:
                                para_parts.append(part)

                        combined_text = "".join(para_parts)

                        # Use left alignment if multiple code elements
                        if code_count >= 2:
                            left_style = ParagraphStyle(
                                "TempLeft",
                                parent=self.styles["CustomBody"],
                                alignment=TA_LEFT,
                            )
                            story.append(Paragraph(combined_text, left_style))
                        else:
                            story.append(
                                Paragraph(combined_text, self.styles["CustomBody"])
                            )
                    else:
                        # Check paragraph length for justification
                        if len(para_text) < 150:
                            left_style = ParagraphStyle(
                                "TempLeft",
                                parent=self.styles["CustomBody"],
                                alignment=TA_LEFT,
                            )
                            story.append(Paragraph(para_text, left_style))
                        else:
                            story.append(
                                Paragraph(para_text, self.styles["CustomBody"])
                            )

                elif element.name == "pre":
                    # Code block processing - check for Mermaid diagrams first
                    code_elem = element.find("code")

                    if code_elem:
                        # Check if this is a Mermaid diagram
                        classes = code_elem.get("class") or []
                        is_mermaid = any(
                            "mermaid" in str(c).lower()
                            for c in (
                                classes if isinstance(classes, list) else [classes]
                            )
                        )

                        # Get Mermaid config
                        mermaid_config = self.config.get("mermaid", {})

                        if is_mermaid and mermaid_config.get("enabled", True):
                            # Extract Mermaid code
                            mermaid_code = code_elem.get_text().strip()
                            self.logger.info(
                                f"Detected Mermaid diagram ({len(mermaid_code)} chars)"
                            )

                            # Try to render Mermaid diagram
                            img_path = self._render_mermaid_diagram(mermaid_code)

                            if img_path:
                                try:
                                    # Open image to get dimensions
                                    img = Image.open(img_path)
                                    img_width, img_height = img.size

                                    # Calculate scaling to fit page width (with margins)
                                    page_width = (
                                        A4[0]
                                        - (
                                            self.config["margins"]["left"]
                                            + self.config["margins"]["right"]
                                        )
                                        * mm
                                    )

                                    # Calculate available height (accounting for margins and spacing)
                                    page_height = (
                                        A4[1]
                                        - (
                                            self.config["margins"]["top"]
                                            + self.config["margins"]["bottom"]
                                        )
                                        * mm
                                        - 72  # Reserve space for header/footer (1 inch)
                                    )

                                    max_width_percent = mermaid_config.get(
                                        "max_width_percent", 95
                                    )
                                    max_width = page_width * (max_width_percent / 100)

                                    # Calculate scaled dimensions maintaining aspect ratio
                                    aspect_ratio = img_height / img_width

                                    # Start with width-based scaling
                                    if img_width > max_width:
                                        scaled_width = max_width
                                        scaled_height = max_width * aspect_ratio
                                    else:
                                        # Convert pixels to points (assuming 72 DPI)
                                        scaled_width = img_width * 0.75
                                        scaled_height = img_height * 0.75

                                    # Check if height exceeds page height and scale down further if needed
                                    if scaled_height > page_height:
                                        scale_factor = page_height / scaled_height
                                        scaled_height = page_height
                                        scaled_width = scaled_width * scale_factor
                                        self.logger.debug(
                                            f"Scaled diagram to fit page: "
                                            f"{scaled_width:.0f}x{scaled_height:.0f}"
                                        )

                                    # Create ReportLab image
                                    rl_img = RLImage(
                                        img_path,
                                        width=scaled_width,
                                        height=scaled_height,
                                    )

                                    # Add to story with spacing, kept together
                                    story.append(KeepTogether([
                                        Spacer(1, 0.1 * inch),
                                        rl_img,
                                        Spacer(1, 0.2 * inch),
                                    ]))

                                    self.logger.info(
                                        f"Added Mermaid diagram: {scaled_width:.0f}x{scaled_height:.0f} points"
                                    )

                                    # Track temp file for cleanup after PDF is built
                                    self.temp_files.append(img_path)
                                    self.logger.debug(
                                        f"Tracking temp image for later cleanup: {img_path}"
                                    )

                                    # Skip regular code block processing
                                    continue

                                except Exception as e:
                                    self.logger.error(
                                        f"Failed to insert Mermaid image: {e}"
                                    )
                                    # Fall through to regular code block processing
                            else:
                                # Rendering failed, fall through to show as code block
                                self.logger.warning(
                                    "Mermaid rendering failed, displaying as code block"
                                )

                    # Regular code block processing (or Mermaid fallback)
                    code_text = element.get_text().strip()

                    if code_elem:
                        code_text = code_elem.get_text().strip()

                    # Detect language for styling
                    lang = self._detect_code_language(code_elem)
                    if lang:
                        self.logger.debug(f"Code block language: {lang}")

                    # Process and style code lines
                    lines = code_text.split("\n")
                    if lines:
                        content_html, style_name = self._render_code_block(lines, lang)
                        story.append(KeepTogether([
                            Paragraph(
                                content_html,
                                self.styles[style_name],
                            ),
                            Spacer(1, 0.1 * inch),
                        ]))

                elif element.name == "div" and "highlight" in (
                    element.get("class") or []
                ):
                    # Handle highlighted code blocks
                    code_elem = element.find("pre")
                    inner_code = None
                    if code_elem:
                        inner_code = code_elem.find("code")
                    lang = self._detect_code_language(inner_code or code_elem)
                    if code_elem:
                        code_text = code_elem.get_text().strip()
                        lines = code_text.split("\n")
                        if lines:
                            content_html, style_name = self._render_code_block(
                                lines, lang
                            )
                            story.append(KeepTogether([
                                Paragraph(
                                    content_html,
                                    self.styles[style_name],
                                ),
                                Spacer(1, 0.1 * inch),
                            ]))

                elif element.name == "blockquote":
                    quote_text = element.get_text()
                    story.append(KeepTogether([
                        Paragraph(quote_text, self.styles["CustomQuote"]),
                        Spacer(1, 0.1 * inch),
                    ]))

                elif element.name == "ul" or element.name == "ol":
                    self._process_list_element(element, story, depth=0)
                    story.append(Spacer(1, 0.1 * inch))

                elif element.name == "table":
                    # Process tables with width-fitting and text wrapping
                    raw_rows = []
                    for row in element.find_all("tr"):
                        row_data = []
                        for cell in row.find_all(["th", "td"]):
                            row_data.append(cell.get_text())
                        raw_rows.append(row_data)

                    if raw_rows:
                        num_cols = max(len(r) for r in raw_rows)

                        # Pad short rows so every row has the same column count
                        for r in raw_rows:
                            while len(r) < num_cols:
                                r.append("")

                        # Available page width (points)
                        available_width = (
                            A4[0]
                            - (
                                self.config["margins"]["left"]
                                + self.config["margins"]["right"]
                            )
                            * mm
                        )

                        # For wide tables (>6 cols), use a smaller font
                        if num_cols > 6:
                            cell_style = ParagraphStyle(
                                "TableCellSmall",
                                parent=self.styles["TableCell"],
                                fontSize=7.5,
                                leading=10,
                            )
                            header_style = ParagraphStyle(
                                "TableCellHeaderSmall",
                                parent=self.styles["TableCellHeader"],
                                fontSize=7.5,
                                leading=10,
                            )
                        else:
                            cell_style = self.styles["TableCell"]
                            header_style = self.styles["TableCellHeader"]

                        # Measure natural column widths (approximate)
                        char_width = cell_style.fontSize * 0.5
                        natural_widths = [0.0] * num_cols
                        for r in raw_rows:
                            for ci, val in enumerate(r):
                                w = len(val) * char_width + 12  # 12pt padding
                                if w > natural_widths[ci]:
                                    natural_widths[ci] = w

                        total_natural = sum(natural_widths)
                        min_col_width = 40  # points

                        if total_natural <= available_width:
                            col_widths = natural_widths
                        else:
                            # Scale proportionally, respecting minimum
                            col_widths = [
                                max(min_col_width, w * available_width / total_natural)
                                for w in natural_widths
                            ]
                            # If minimums pushed total over budget, re-scale the non-minimum cols
                            total_after = sum(col_widths)
                            if total_after > available_width:
                                excess = total_after - available_width
                                scalable = [
                                    i
                                    for i, w in enumerate(col_widths)
                                    if w > min_col_width
                                ]
                                scalable_total = sum(col_widths[i] for i in scalable)
                                if scalable_total > 0:
                                    for i in scalable:
                                        col_widths[i] -= excess * (
                                            col_widths[i] / scalable_total
                                        )
                                        col_widths[i] = max(
                                            min_col_width, col_widths[i]
                                        )

                        # Wrap cell text in Paragraph objects for word-wrapping
                        table_data = []
                        for ri, r in enumerate(raw_rows):
                            styled_row = []
                            is_header = ri == 0
                            style = header_style if is_header else cell_style
                            for val in r:
                                # Escape XML entities for ReportLab Paragraph
                                safe = (
                                    val.replace("&", "&amp;")
                                    .replace("<", "&lt;")
                                    .replace(">", "&gt;")
                                )
                                styled_row.append(Paragraph(safe, style))
                            table_data.append(styled_row)

                        # Config colors with fallbacks
                        color_cfg = self.config.get("colors", {})
                        header_bg = colors.HexColor(
                            color_cfg.get("table_header", "#f6f8fa")
                        )
                        border_color = colors.HexColor(
                            color_cfg.get("table_border", "#e1e4e8")
                        )

                        t = Table(table_data, colWidths=col_widths, repeatRows=1)
                        t.setStyle(
                            TableStyle(
                                [
                                    ("BACKGROUND", (0, 0), (-1, 0), header_bg),
                                    ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                                    ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                                    ("BOTTOMPADDING", (0, 1), (-1, -1), 4),
                                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                                    ("GRID", (0, 0), (-1, -1), 0.5, border_color),
                                ]
                            )
                        )
                        story.append(KeepTogether([t, Spacer(1, 0.2 * inch)]))

        self.logger.info(f"Generated {len(story)} story elements")
        return story

    def _create_cover_page(self, canvas_obj, doc, metadata: Dict[str, str]):
        """Create a cover page for the document."""
        self.logger.debug("Creating cover page")
        canvas_obj.saveState()

        # Set page size
        width, height = A4

        # Use config margins to match body pages
        left_margin = self.config["margins"]["left"] * mm
        right_margin = self.config["margins"]["right"] * mm
        usable_width = width - left_margin - right_margin

        # Add logo if exists
        logos = self.config.get("logos", {})
        cover_logo = logos.get("cover", "GerdsenAI_Neural_G_Invoice.png")
        logo_path = self.assets_dir / cover_logo
        logo_bottom = height - 3.5 * inch

        if logo_path.exists():
            try:
                img = Image.open(logo_path)
                aspect = img.height / img.width
                img_width = 2.5 * inch
                img_height = img_width * aspect
                canvas_obj.drawImage(
                    str(logo_path),
                    (width - img_width) / 2,
                    height - 2 * inch - img_height,
                    width=img_width,
                    height=img_height,
                    preserveAspectRatio=True,
                    mask="auto",
                )
                logo_bottom = height - 2 * inch - img_height - 1.5 * inch
                self.logger.debug("Logo added to cover page")
            except Exception as e:
                self.logger.warning(f"Could not add logo: {e}")

        # Title
        title = metadata.get("title", "Untitled Document")

        # Word wrap the title with font-size cascade and iterative fit
        title_font_name = "Helvetica-Bold"
        for title_font_size in [28, 24, 20]:
            char_width = title_font_size * 0.55
            max_chars = max(10, int(usable_width / char_width))
            lines = textwrap.wrap(title, width=max_chars, break_long_words=False)
            # Iteratively tighten until all lines fit within usable_width
            all_fit = False
            for _ in range(10):
                all_fit = all(
                    canvas_obj.stringWidth(line, title_font_name, title_font_size) <= usable_width
                    for line in lines
                )
                if all_fit:
                    break
                max_chars = max(10, int(max_chars * 0.85))
                lines = textwrap.wrap(title, width=max_chars, break_long_words=False)
            if all_fit:
                break

        canvas_obj.setFont(title_font_name, title_font_size)
        canvas_obj.setFillColor(colors.HexColor("#1a1a1a"))

        # Draw title lines
        y_position = logo_bottom
        line_height = title_font_size * 1.4

        for line in lines:
            canvas_obj.drawCentredString(width / 2, y_position, line)
            y_position -= line_height

        # Subtitle if present
        if metadata.get("subtitle"):
            y_position -= 0.2 * inch
            subtitle_font_name = "Helvetica"
            # Inset subtitle slightly from page margins for breathing room
            subtitle_usable = usable_width - 20 * mm
            canvas_obj.setFillColor(colors.HexColor("#666666"))

            # Font-size cascade with iterative fit
            for subtitle_font_size in [16, 14, 12]:
                sub_char_width = subtitle_font_size * 0.55
                subtitle_max_chars = max(15, int(subtitle_usable / sub_char_width))
                subtitle_lines = textwrap.wrap(
                    metadata["subtitle"], width=subtitle_max_chars, break_long_words=False
                )
                # Iteratively tighten until all lines fit
                all_fit = False
                for _ in range(10):
                    all_fit = all(
                        canvas_obj.stringWidth(line, subtitle_font_name, subtitle_font_size) <= subtitle_usable
                        for line in subtitle_lines
                    )
                    if all_fit:
                        break
                    subtitle_max_chars = max(15, int(subtitle_max_chars * 0.85))
                    subtitle_lines = textwrap.wrap(
                        metadata["subtitle"], width=subtitle_max_chars, break_long_words=False
                    )
                if all_fit:
                    break

            canvas_obj.setFont(subtitle_font_name, subtitle_font_size)
            sub_line_height = subtitle_font_size * 1.5
            for line in subtitle_lines:
                canvas_obj.drawCentredString(width / 2, y_position, line)
                y_position -= sub_line_height

        # Author
        canvas_obj.setFont("Helvetica-Bold", 14)
        canvas_obj.setFillColor(colors.HexColor("#444444"))
        author_text = f"Prepared by {metadata.get('author', 'Unknown Author')}"
        author_width = canvas_obj.stringWidth(author_text, "Helvetica-Bold", 14)
        if author_width > usable_width:
            author_lines = textwrap.wrap(author_text, width=int(usable_width / 14 * 2))
            y_pos = 3 * inch
            for line in author_lines:
                canvas_obj.drawCentredString(width / 2, y_pos, line)
                y_pos -= 0.25 * inch
        else:
            canvas_obj.drawCentredString(width / 2, 3 * inch, author_text)

        # Date
        canvas_obj.setFont("Helvetica", 11)
        canvas_obj.setFillColor(colors.HexColor("#888888"))
        canvas_obj.drawCentredString(
            width / 2,
            1.5 * inch,
            metadata.get("date", datetime.now().strftime("%B %d, %Y")),
        )

        # Version
        canvas_obj.setFont("Helvetica", 10)
        canvas_obj.setFillColor(colors.HexColor("#aaaaaa"))
        canvas_obj.drawCentredString(
            width / 2, 1 * inch, f"Version {metadata.get('version', '1.0.0')}"
        )

        canvas_obj.restoreState()

    def _add_page_number(self, canvas_obj, doc):
        """Add page numbers and headers to each page."""
        canvas_obj.saveState()

        # Skip header/footer on first page
        if doc.page > 1:
            width, height = A4

            # Header - document title
            if hasattr(doc, "metadata"):
                canvas_obj.setFont("Helvetica", 10)
                canvas_obj.setFillColor(colors.HexColor("#666666"))
                canvas_obj.drawCentredString(
                    width / 2, height - 0.5 * inch, doc.metadata.get("title", "")
                )

            # Footer - page number
            canvas_obj.setFont("Helvetica", 9)
            canvas_obj.setFillColor(colors.HexColor("#666666"))
            canvas_obj.drawRightString(width - inch, 0.5 * inch, f"Page {doc.page - 1}")

            # Footer - logo
            logos = self.config.get("logos", {})
            footer_logo = logos.get(
                "footer",
                "GerdsenAI_Neural_G_Invoice.png",
            )
            logo_path = self.assets_dir / footer_logo
            if logo_path.exists():
                try:
                    canvas_obj.drawImage(
                        str(logo_path),
                        width / 2 - 0.5 * inch,
                        0.3 * inch,
                        width=inch,
                        height=0.4 * inch,
                        preserveAspectRatio=True,
                        mask="auto",
                    )
                except Exception:
                    pass

        canvas_obj.restoreState()

    def _resolve_input_path(self, input_file: str) -> Path:
        """Resolve input file path with robust handling of different path formats."""
        self.logger.debug(f"Resolving input path for: {input_file}")

        # Convert to Path object
        input_path = Path(input_file)

        # Case 1: Absolute path - use directly
        if input_path.is_absolute():
            self.logger.debug(f"Using absolute path: {input_path}")
            return input_path

        # Case 2: Relative path that exists as-is - use directly
        if input_path.exists():
            self.logger.debug(f"Using existing relative path: {input_path}")
            return input_path.resolve()

        # Case 3: Path already includes To_Build/ - avoid double-prepending
        if str(input_path).startswith("To_Build/") or str(input_path).startswith(
            "TO_Build/"
        ):
            # Remove the To_Build prefix and treat as bare filename
            parts = input_path.parts
            if len(parts) > 1:
                filename = parts[-1]  # Get just the filename
                resolved_path = self.to_build_dir / filename
                self.logger.debug(f"Removed To_Build prefix, using: {resolved_path}")
                return resolved_path

        # Case 4: Bare filename - prepend To_Build directory
        resolved_path = self.to_build_dir / input_file
        self.logger.debug(f"Using To_Build directory path: {resolved_path}")
        return resolved_path

    def build_document(self, input_file: str, output_file: Optional[str] = None) -> str:
        """Build a PDF document from input file."""
        self.logger.info("=" * 60)
        self.logger.info(f"Building document: {input_file}")

        try:
            # Robust input path resolution
            input_path = self._resolve_input_path(input_file)

            if not input_path.exists():
                error_msg = f"Input file not found: {input_path}"
                self.logger.error(error_msg)
                raise FileNotFoundError(error_msg)

            # Read content
            self.logger.debug(f"Reading file: {input_path}")
            with open(input_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Extract metadata
            content, metadata = self._extract_metadata(content)
            self.logger.info(f"Document title: {metadata.get('title', 'Untitled')}")

            # Generate output filename
            if output_file is None:
                base_name = input_path.stem
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                prefix = self.config.get("filename_prefix", "")
                output_file = f"{prefix}{base_name}_{timestamp}.pdf"

            output_path = self.output_dir / output_file
            self.logger.info(f"Output file: {output_path}")

            # Reset heading counter and figure counter for new document
            self.heading_counter = 0
            self.figure_counter = 0
            self._source_dir = input_path.parent

            # Create TOC for markdown files
            toc = None
            suffix_lower = input_path.suffix.lower()
            if suffix_lower in (".md", ".markdown"):
                toc = self._create_toc()
                self.logger.debug("Created TOC for markdown document")

            # Create PDF document with custom template for TOC support
            doc = TOCDocTemplate(
                str(output_path),
                pagesize=A4,
                rightMargin=self.config["margins"]["right"] * mm,
                leftMargin=self.config["margins"]["left"] * mm,
                topMargin=self.config["margins"]["top"] * mm,
                bottomMargin=self.config["margins"]["bottom"] * mm,
                title=metadata.get("title", "Document"),
                author=metadata.get("author", "Unknown"),
                subject=metadata.get("subject", ""),
                creator="GerdsenAI Document Builder",
                toc=toc,  # Pass TOC to the document template
            )

            # Store metadata in doc
            doc.metadata = metadata  # type: ignore[attr-defined]

            # Build story
            story = []

            # Add cover page placeholder
            story.append(PageBreak())

            # Process content
            suffix_lower = input_path.suffix.lower()
            if suffix_lower in (".md", ".markdown"):
                content_story = self._process_markdown_to_story(content, toc)
                story.extend(content_story)
            elif suffix_lower in (".mermaid", ".mmd"):
                # Standalone mermaid diagram
                self.logger.debug("Processing standalone Mermaid diagram")
                img_path = self._render_mermaid_diagram(content)
                if img_path:
                    try:
                        with Image.open(img_path) as pil_img:
                            img_width, img_height = pil_img.size

                        page_width = A4[0] - (
                            self.config["margins"]["left"] * mm
                            + self.config["margins"]["right"] * mm
                        )
                        page_height = A4[1] - (
                            self.config["margins"]["top"] * mm
                            + self.config["margins"]["bottom"] * mm
                        )
                        max_width_pct = (
                            self.config.get("mermaid", {}).get("max_width_percent", 95) / 100
                        )
                        max_width = page_width * max_width_pct

                        aspect_ratio = img_height / img_width
                        if img_width > max_width / 0.75:
                            scaled_width = max_width
                            scaled_height = max_width * aspect_ratio
                        else:
                            scaled_width = img_width * 0.75
                            scaled_height = img_height * 0.75

                        if scaled_height > page_height:
                            scale_factor = page_height / scaled_height
                            scaled_height = page_height
                            scaled_width = scaled_width * scale_factor

                        rl_img = RLImage(img_path, width=scaled_width, height=scaled_height)
                        story.append(Spacer(1, 0.2 * inch))
                        story.append(rl_img)

                        self.temp_files.append(img_path)
                    except Exception as e:
                        self.logger.error(f"Failed to process mermaid diagram: {e}")
                        raise
                else:
                    raise RuntimeError(
                        f"Mermaid rendering failed for {input_path.name}"
                    )
            else:
                # Plain text
                self.logger.debug("Processing plain text document")
                paragraphs = content.split("\n\n")
                for para in paragraphs:
                    if para.strip():
                        story.append(
                            Paragraph(
                                para.replace("\n", "<br/>"), self.styles["CustomBody"]
                            )
                        )
                        story.append(Spacer(1, 0.1 * inch))

            # Build PDF with custom canvas for page tracking
            def make_canvas(*args, **kwargs):
                canv = NumberedCanvas(*args, **kwargs)
                canv.toc = toc  # type: ignore[attr-defined]
                return canv

            # Page handlers
            def on_every_page(canvas_obj, doc):
                if doc.page == 1:
                    self._create_cover_page(canvas_obj, doc, metadata)
                else:
                    self._add_page_number(canvas_obj, doc)

            # Build with custom canvas
            self.logger.info("Building PDF...")
            doc.multiBuild(
                story,
                canvasmaker=make_canvas,
                onFirstPage=on_every_page,
                onLaterPages=on_every_page,
            )

            self.logger.info(f"[OK] Successfully generated PDF: {output_path}")

            # Clean up temporary files now that PDF is built
            for temp_file in self.temp_files:
                try:
                    if Path(temp_file).exists():
                        Path(temp_file).unlink()
                        self.logger.debug(f"Cleaned up temp file: {temp_file}")
                except Exception as e:
                    self.logger.warning(f"Failed to cleanup temp file {temp_file}: {e}")

            # Clear the list for next build
            self.temp_files = []

            return str(output_path)

        except Exception as e:
            self.logger.error(f"[FAIL] Error building document: {e}")
            self.logger.error(traceback.format_exc())

            # Clean up temporary files even on error
            for temp_file in self.temp_files:
                try:
                    if Path(temp_file).exists():
                        Path(temp_file).unlink()
                        self.logger.debug(
                            f"Cleaned up temp file (error path): {temp_file}"
                        )
                except Exception as cleanup_error:
                    self.logger.warning(
                        f"Failed to cleanup temp file {temp_file}: {cleanup_error}"
                    )

            # Clear the list
            self.temp_files = []

            raise

    def build_all_documents(self) -> List[str]:
        """Build all documents in the To_Build directory."""
        self.logger.info("=" * 60)
        self.logger.info("Building all documents")

        output_files = []
        success_count = 0
        error_count = 0

        # Get all markdown and text files
        files = list(self.to_build_dir.glob("*"))
        valid_files = [
            f for f in files if f.suffix.lower() in {".md", ".markdown", ".txt", ".mermaid", ".mmd"}
        ]

        self.logger.info(f"Found {len(valid_files)} documents to build")

        for file_path in valid_files:
            try:
                self.logger.info(f"[BUILD] Building: {file_path.name}")
                output = self.build_document(file_path.name)
                output_files.append(output)
                success_count += 1
            except Exception as e:
                error_count += 1
                self.logger.error(f"[FAIL] Error building {file_path.name}: {e}")
                self.logger.error(traceback.format_exc())

        # Summary
        self.logger.info("=" * 60)
        self.logger.info("Build Summary:")
        self.logger.info(f"  [OK] Successful: {success_count}")
        self.logger.info(f"  [FAIL] Failed: {error_count}")
        self.logger.info(f"  [INFO] Total: {len(valid_files)}")
        self.logger.info("=" * 60)

        return output_files


def main():
    """Main entry point for the document builder."""
    parser = argparse.ArgumentParser(
        description="GerdsenAI Document Builder - Convert Markdown/Text to Professional PDFs"
    )
    parser.add_argument(
        "input_file",
        nargs="?",
        help="Input file name (from To_Build directory). If not specified, builds all files.",
    )
    parser.add_argument("-o", "--output", help="Output PDF file name")
    parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="Build all documents in To_Build directory",
    )
    parser.add_argument(
        "--repo-path",
        default=str(Path(__file__).resolve().parent),
        help="Repository path",
    )

    args = parser.parse_args()

    try:
        builder = DocumentBuilder(args.repo_path)

        if args.all or args.input_file is None:
            print("Building all documents...")
            output_files = builder.build_all_documents()
            print(f"\nGenerated {len(output_files)} PDF(s)")
        else:
            builder.build_document(args.input_file, args.output)
            print("\nPDF generated successfully!")

    except Exception as e:
        print(f"[FAIL] Error: {e}")
        logging.getLogger("DocumentBuilder").error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
