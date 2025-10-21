#!/usr/bin/env python3
"""
GerdsenAI Document Builder
A world-class document builder that converts Markdown/Text files to professional PDFs
with custom styling, working Table of Contents, and comprehensive logging.
"""

import os
import sys
import argparse
import re
import base64
import tempfile
import subprocess
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple, Union
import io
import traceback
import textwrap

# Third-party imports
import markdown
from mermaid_cli import render_mermaid_file_sync
from markdown.extensions import (
    tables,
    fenced_code,
    footnotes,
    attr_list,
    def_list,
    abbr,
    toc,
)
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
from reportlab.platypus import Table, TableStyle, PageBreak, KeepTogether
from reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate
from reportlab.platypus.frames import Frame
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
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
                    yaml_config = yaml.safe_load(f)
                    if yaml_config and "default" in yaml_config:
                        default_config.update(yaml_config["default"])
                    if "margins" in yaml_config:
                        default_config["margins"] = yaml_config["margins"]
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
                spaceAfter=12,
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
                spaceAfter=10,
            ),
            "CustomHeading3": ParagraphStyle(
                "CustomHeading3",
                parent=styles["Heading3"],
                fontName="Helvetica",
                fontSize=14,
                textColor=colors.HexColor("#34495e"),
                spaceBefore=12,
                spaceAfter=8,
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
            "CustomCode": ParagraphStyle(
                "CustomCode",
                parent=styles["Code"],
                fontName="Courier",
                fontSize=9,
                textColor=colors.HexColor("#00ff00"),
                backColor=colors.HexColor("#000000"),
                borderColor=colors.HexColor("#333333"),
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
                textColor=colors.HexColor("#00c853"),
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

                # Parse front matter
                for line in front_matter.split("\n"):
                    if ":" in line:
                        key, value = line.split(":", 1)
                        metadata[key.strip().lower()] = value.strip()

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

    def _sanitize_mermaid_diagram(self, mermaid_code: str) -> Tuple[str, List[str]]:
        """
        Sanitize Mermaid diagram code to fix common edge cases.

        Args:
            mermaid_code: Raw Mermaid diagram code

        Returns:
            Tuple of (sanitized_code, list_of_fixes_applied)
        """
        original_code = mermaid_code
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

        node_counter = 1

        for line in lines[1:]:
            line = line.strip()
            if not line or line.startswith("%") or line.startswith("//"):
                continue

            # Replace complex labels with simple generic ones
            # Keep the structure but simplify labels
            line = re.sub(r'\["[^"]*"\]', f"[Node]", line)
            line = re.sub(r'\("[^"]*"\)', f"(Node)", line)
            line = re.sub(r"\{[^}]*\}", f"{{Node}}", line)

            simplified.append(line)

        return "\n".join(simplified)

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
                        f"\n⚠️  Auto-fixed Mermaid diagram ({len(unique_fixes)} fix{'es' if len(unique_fixes) != 1 else ''}):"
                    )
                    for fix in unique_fixes:
                        print(f"   ✓ {fix}")
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
            print("   🔄 Rendering diagram...", end="", flush=True)

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

            print(" ✓", flush=True)

            # Verify the file was created
            if not Path(png_path).exists():
                raise FileNotFoundError(
                    f"Mermaid rendering failed - output file not created"
                )

            self.logger.info(f"Successfully rendered Mermaid diagram")
            return png_path

        except ImportError as e:
            self.logger.error(
                f"mermaid-cli not installed. Run: pip install mermaid-cli && playwright install chromium"
            )
            self.logger.error(f"Error: {e}")
            if mermaid_config.get("fallback_to_code", True):
                return None
            raise

        except Exception as e:
            print(" ✗", flush=True)  # Clear progress indicator

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
                        print(f"\n❌ Mermaid diagram rendering failed: {error_summary}")
                        print(
                            f"   Diagram can be rendered in simplified form (structure preserved, labels removed)"
                        )
                        response = (
                            input("   Render simplified diagram? (yes/no/all) [yes]: ")
                            .strip()
                            .lower()
                        )

                        if response == "all":
                            # User wants all future simplified diagrams without prompting
                            mermaid_config["prompt_before_simplified"] = False
                            mermaid_config["auto_accept_simplified"] = True
                            should_render_simplified = True
                            print(
                                "   ✓ Will auto-render all future simplified diagrams without prompting\n"
                            )
                        elif response in ["n", "no"]:
                            should_render_simplified = False
                            self.logger.info(
                                "User declined simplified rendering, falling back to code block"
                            )
                        else:
                            should_render_simplified = True
                    else:
                        # Auto-accepting - show informative message
                        print(f"\n⚠️  Diagram rendering failed: {error_summary}")
                        print(f"   🔄 Automatically rendering simplified version...")

                    if not should_render_simplified:
                        if mermaid_config.get("fallback_to_code", True):
                            return None
                        raise

                    # Create simplified version
                    self.logger.info("Attempting simplified diagram rendering...")
                    if not auto_accept:
                        print(
                            "   🔄 Rendering simplified diagram...", end="", flush=True
                        )

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
                                print(" ✓", flush=True)
                            print("   ✅ Simplified diagram rendered successfully\n")

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
                        f"\n   ❌ Simplified rendering also failed: {error_summary2}\n"
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

    def _process_markdown_to_story(
        self, content: str, toc: Optional[TableOfContents] = None
    ) -> List:
        """Process markdown content and convert to ReportLab story elements."""
        self.logger.info("Processing markdown content to story elements")

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
        headings = soup.find_all(["h1", "h2", "h3"])
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
                if element.name in ["h1", "h2", "h3"]:
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
                    story.append(Spacer(1, 0.2 * inch))

                elif element.name == "h2":
                    text = element.get_text()
                    para = self._create_heading_with_bookmark(
                        text, self.styles["CustomHeading2"], 1
                    )
                    story.append(para)
                    story.append(Spacer(1, 0.15 * inch))

                elif element.name == "h3":
                    text = element.get_text()
                    para = self._create_heading_with_bookmark(
                        text, self.styles["CustomHeading3"], 2
                    )
                    story.append(para)
                    story.append(Spacer(1, 0.1 * inch))

                elif element.name == "p":
                    # Skip paragraphs containing images
                    if element.find("img"):
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
                                    f'<font name="Courier-Bold" size="10" color="#00c853">{code_content}</font>'
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
                                            f"Scaled diagram down to fit page height: {scaled_width:.0f}x{scaled_height:.0f}"
                                        )

                                    # Create ReportLab image
                                    rl_img = RLImage(
                                        img_path,
                                        width=scaled_width,
                                        height=scaled_height,
                                    )

                                    # Add to story with spacing
                                    story.append(Spacer(1, 0.1 * inch))
                                    story.append(rl_img)
                                    story.append(Spacer(1, 0.2 * inch))

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

                    # Process code lines
                    lines = code_text.split("\n")
                    code_lines = []
                    for line in lines:
                        if line.strip():
                            line = line.replace("&", "&amp;")
                            line = line.replace("<", "&lt;")
                            line = line.replace(">", "&gt;")
                            code_lines.append(line)
                        else:
                            code_lines.append("")

                    if code_lines:
                        code_content = "<br/>".join(code_lines)
                        story.append(Paragraph(code_content, self.styles["CustomCode"]))
                        story.append(Spacer(1, 0.1 * inch))

                elif element.name == "div" and "highlight" in (
                    element.get("class") or []
                ):
                    # Handle highlighted code blocks
                    code_elem = element.find("pre")
                    if code_elem:
                        code_text = code_elem.get_text().strip()
                        lines = code_text.split("\n")
                        code_lines = []
                        for line in lines:
                            if line.strip():
                                line = line.replace("&", "&amp;")
                                line = line.replace("<", "&lt;")
                                line = line.replace(">", "&gt;")
                                code_lines.append(line)
                            else:
                                code_lines.append("")

                        if code_lines:
                            code_content = "<br/>".join(code_lines)
                            story.append(
                                Paragraph(code_content, self.styles["CustomCode"])
                            )
                            story.append(Spacer(1, 0.1 * inch))

                elif element.name == "blockquote":
                    quote_text = element.get_text()
                    story.append(Paragraph(quote_text, self.styles["CustomQuote"]))
                    story.append(Spacer(1, 0.1 * inch))

                elif element.name == "ul" or element.name == "ol":
                    for idx, li in enumerate(
                        element.find_all("li", recursive=False), 1
                    ):
                        bullet = "• " if element.name == "ul" else f"{idx}. "
                        text = bullet + li.get_text()
                        story.append(Paragraph(text, self.styles["CustomBody"]))
                    story.append(Spacer(1, 0.1 * inch))

                elif element.name == "table":
                    # Process tables
                    table_data = []
                    for row in element.find_all("tr"):
                        row_data = []
                        for cell in row.find_all(["th", "td"]):
                            row_data.append(cell.get_text())
                        table_data.append(row_data)

                    if table_data:
                        t = Table(table_data)
                        t.setStyle(
                            TableStyle(
                                [
                                    (
                                        "BACKGROUND",
                                        (0, 0),
                                        (-1, 0),
                                        colors.HexColor("#f6f8fa"),
                                    ),
                                    (
                                        "TEXTCOLOR",
                                        (0, 0),
                                        (-1, 0),
                                        colors.HexColor("#1a1a1a"),
                                    ),
                                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                                    ("FONTSIZE", (0, 0), (-1, 0), 10),
                                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                                    ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                                    (
                                        "GRID",
                                        (0, 0),
                                        (-1, -1),
                                        1,
                                        colors.HexColor("#e1e4e8"),
                                    ),
                                    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                                    ("FONTSIZE", (0, 1), (-1, -1), 9),
                                    ("PADDING", (0, 0), (-1, -1), 6),
                                ]
                            )
                        )
                        story.append(t)
                        story.append(Spacer(1, 0.2 * inch))

        self.logger.info(f"Generated {len(story)} story elements")
        return story

    def _create_cover_page(self, canvas_obj, doc, metadata: Dict[str, str]):
        """Create a cover page for the document."""
        self.logger.debug("Creating cover page")
        canvas_obj.saveState()

        # Set page size
        width, height = A4

        # Define margins
        margin = 1 * inch
        usable_width = width - (2 * margin)

        # Add logo if exists
        logo_path = self.assets_dir / "GerdsenAI_Neural_G_Invoice.png"
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

        # Word wrap the title
        import textwrap

        title_font_size = 28
        char_width = title_font_size * 0.6
        max_chars = int(usable_width / char_width * 1.8)

        lines = textwrap.wrap(title, width=max_chars, break_long_words=False)

        # Check if we need smaller font
        use_smaller_font = False
        for line in lines:
            test_width = canvas_obj.stringWidth(line, "Helvetica-Bold", title_font_size)
            if test_width > usable_width:
                use_smaller_font = True
                break

        if use_smaller_font:
            title_font_size = 24

        canvas_obj.setFont("Helvetica-Bold", title_font_size)
        canvas_obj.setFillColor(colors.HexColor("#1a1a1a"))

        # Draw title lines
        y_position = logo_bottom
        line_height = 0.4 * inch

        for line in lines:
            canvas_obj.drawCentredString(width / 2, y_position, line)
            y_position -= line_height

        # Subtitle if present
        if metadata.get("subtitle"):
            y_position -= 0.2 * inch
            canvas_obj.setFont("Helvetica", 16)
            canvas_obj.setFillColor(colors.HexColor("#666666"))
            subtitle_char_width = 16 * 0.5
            subtitle_max_chars = int(usable_width / subtitle_char_width * 1.8)
            subtitle_lines = textwrap.wrap(
                metadata["subtitle"], width=subtitle_max_chars
            )
            for line in subtitle_lines:
                canvas_obj.drawCentredString(width / 2, y_position, line)
                y_position -= 0.3 * inch

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
            logo_path = self.assets_dir / "GerdsenAI_Neural_G_Invoice.png"
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
                except:
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

            # Reset heading counter for new document
            self.heading_counter = 0

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

            self.logger.info(f"✅ Successfully generated PDF: {output_path}")

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
            self.logger.error(f"❌ Error building document: {e}")
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
            f for f in files if f.suffix.lower() in {".md", ".markdown", ".txt"}
        ]

        self.logger.info(f"Found {len(valid_files)} documents to build")

        for file_path in valid_files:
            try:
                self.logger.info(f"📄 Building: {file_path.name}")
                output = self.build_document(file_path.name)
                output_files.append(output)
                success_count += 1
            except Exception as e:
                error_count += 1
                self.logger.error(f"❌ Error building {file_path.name}: {e}")
                self.logger.error(traceback.format_exc())

        # Summary
        self.logger.info("=" * 60)
        self.logger.info(f"Build Summary:")
        self.logger.info(f"  ✅ Successful: {success_count}")
        self.logger.info(f"  ❌ Failed: {error_count}")
        self.logger.info(f"  📄 Total: {len(valid_files)}")
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
        default="/Volumes/M2 Raid0/GerdsenAI_Repositories/GerdsenAI_Document_Builder",
        help="Repository path",
    )

    args = parser.parse_args()

    try:
        builder = DocumentBuilder(args.repo_path)

        if args.all or args.input_file is None:
            print("🚀 Building all documents...")
            output_files = builder.build_all_documents()
            print(f"\n✨ Generated {len(output_files)} PDF(s)")
        else:
            output = builder.build_document(args.input_file, args.output)
            print(f"\n✨ PDF generated successfully!")

    except Exception as e:
        print(f"❌ Error: {e}")
        logging.getLogger("DocumentBuilder").error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
