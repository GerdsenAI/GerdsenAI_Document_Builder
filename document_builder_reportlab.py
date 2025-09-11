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
from typing import Optional, Dict, Any, List, Tuple
import io
import traceback

# Third-party imports
import markdown
from markdown.extensions import tables, fenced_code, footnotes, attr_list, def_list, abbr, toc
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
from bs4 import BeautifulSoup
import yaml


def setup_logging(repo_path: Path) -> logging.Logger:
    """Setup comprehensive logging system."""
    log_dir = repo_path / "Logs"
    log_dir.mkdir(exist_ok=True)
    
    # Create logger
    logger = logging.getLogger('DocumentBuilder')
    logger.setLevel(logging.DEBUG)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    
    # File handler with rotation
    log_file = log_dir / f"document_builder_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
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
    
    logger.info("="*60)
    logger.info("Document Builder Started")
    logger.info(f"Log file: {log_file}")
    logger.info("="*60)
    
    return logger


class NumberedCanvas(canvas.Canvas):
    """Custom canvas that tracks page numbers for TOC."""
    
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self.page_num = 0
        self.toc = None
        self.logger = logging.getLogger('DocumentBuilder.Canvas')
        
    def showPage(self):
        """Called at the end of each page."""
        self.page_num += 1
        self.logger.debug(f"Page {self.page_num} completed")
        canvas.Canvas.showPage(self)


class TOCDocTemplate(SimpleDocTemplate):
    """Custom document template that properly handles TOC notifications."""
    
    def __init__(self, *args, **kwargs):
        self.toc = kwargs.pop('toc', None)
        self.heading_entries = []  # Store heading info during first pass
        SimpleDocTemplate.__init__(self, *args, **kwargs)
        self.logger = logging.getLogger('DocumentBuilder.DocTemplate')
        
    def afterFlowable(self, flowable):
        """Called after each flowable is rendered."""
        # Create bookmark if the flowable has a bookmark name
        if hasattr(flowable, '_bookmarkName'):
            bookmark_name = flowable._bookmarkName
            # Create a bookmark at the current position in the PDF
            self.canv.bookmarkPage(bookmark_name)
            # Add to outline (PDF bookmarks visible in PDF readers)
            if hasattr(flowable, '__toc_entry__'):
                level, text, _ = flowable.__toc_entry__
                self.canv.addOutlineEntry(text, bookmark_name, level=level)
            self.logger.debug(f"Created bookmark: {bookmark_name}")
        
        # Check if this is a heading with TOC entry
        if hasattr(flowable, '__toc_entry__'):
            level, text, bookmark = flowable.__toc_entry__
            # Get current page number from canvas
            if hasattr(self.canv, 'page_num'):
                page_num = self.canv.page_num
            else:
                page_num = self.page
            
            self.logger.debug(f"TOC Entry detected: Level {level}, Page {page_num}, Text: {text}")
            
            # Store entry for second pass
            self.heading_entries.append((level, text, page_num, bookmark))
            
            # Notify the TOC
            if self.toc:
                self.notify('TOCEntry', (level, text, page_num, bookmark))
    
    def notify(self, kind, stuff):
        """Handle TOC notifications."""
        if kind == 'TOCEntry':
            level, text, page_num, bookmark = stuff
            if self.toc and hasattr(self.toc, 'addEntry'):
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
            "filename_prefix": "GerdsenAI_"
        }
        
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    yaml_config = yaml.safe_load(f)
                    if yaml_config and 'default' in yaml_config:
                        default_config.update(yaml_config['default'])
                    if 'margins' in yaml_config:
                        default_config['margins'] = yaml_config['margins']
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
    
    def _setup_styles(self) -> Dict[str, ParagraphStyle]:
        """Setup paragraph styles for the document."""
        self.logger.debug("Setting up document styles")
        styles = getSampleStyleSheet()
        
        # Custom styles
        custom_styles = {
            'CustomTitle': ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontName='Helvetica-Bold',
                fontSize=24,
                textColor=colors.HexColor('#1a1a1a'),
                spaceAfter=30,
                alignment=TA_CENTER
            ),
            'CustomHeading1': ParagraphStyle(
                'CustomHeading1',
                parent=styles['Heading1'],
                fontName='Helvetica-Bold',
                fontSize=20,
                textColor=colors.HexColor('#1a1a1a'),
                spaceBefore=24,
                spaceAfter=12,
                borderColor=colors.HexColor('#e1e4e8'),
                borderWidth=0,
                borderPadding=0
            ),
            'CustomHeading2': ParagraphStyle(
                'CustomHeading2',
                parent=styles['Heading2'],
                fontName='Helvetica-Bold',
                fontSize=16,
                textColor=colors.HexColor('#2c3e50'),
                spaceBefore=18,
                spaceAfter=10
            ),
            'CustomHeading3': ParagraphStyle(
                'CustomHeading3',
                parent=styles['Heading3'],
                fontName='Helvetica',
                fontSize=14,
                textColor=colors.HexColor('#34495e'),
                spaceBefore=12,
                spaceAfter=8
            ),
            'CustomBody': ParagraphStyle(
                'CustomBody',
                parent=styles['BodyText'],
                fontName='Helvetica',
                fontSize=11,
                textColor=colors.HexColor('#2c3e50'),
                alignment=TA_JUSTIFY,
                spaceBefore=6,
                spaceAfter=6,
                leading=14,
                wordWrap='LTR',
                splitLongWords=1,
                bulletIndent=0,
                leftIndent=0,
                rightIndent=0
            ),
            'CustomCode': ParagraphStyle(
                'CustomCode',
                parent=styles['Code'],
                fontName='Courier',
                fontSize=9,
                textColor=colors.HexColor('#00ff00'),
                backColor=colors.HexColor('#000000'),
                borderColor=colors.HexColor('#333333'),
                borderWidth=1,
                borderPadding=8,
                leftIndent=0,
                rightIndent=0,
                spaceAfter=12,
                spaceBefore=12
            ),
            'CustomInlineCode': ParagraphStyle(
                'CustomInlineCode',
                parent=styles['Normal'],
                fontName='Courier-Bold',
                fontSize=10,
                textColor=colors.HexColor('#00c853'),
            ),
            'CustomQuote': ParagraphStyle(
                'CustomQuote',
                parent=styles['BodyText'],
                fontName='Helvetica',
                fontSize=11,
                textColor=colors.HexColor('#555555'),
                leftIndent=20,
                rightIndent=20,
                spaceBefore=12,
                spaceAfter=12,
                borderColor=colors.HexColor('#3498db'),
                borderWidth=0,
                borderPadding=12,
                backColor=colors.HexColor('#f8f9fa')
            ),
            'TOCHeading': ParagraphStyle(
                'TOCHeading',
                parent=styles['Heading1'],
                fontName='Helvetica-Bold',
                fontSize=24,
                spaceAfter=20,
                textColor=colors.HexColor('#1a1a1a'),
                alignment=TA_CENTER
            ),
            'TOCEntry1': ParagraphStyle(
                'TOCEntry1',
                parent=styles['Normal'],
                fontName='Helvetica',
                fontSize=12,
                leftIndent=0,
                rightIndent=30,
                spaceAfter=6,
                textColor=colors.HexColor('#0066cc')  # Blue for links
            ),
            'TOCEntry2': ParagraphStyle(
                'TOCEntry2',
                parent=styles['Normal'],
                fontName='Helvetica',
                fontSize=11,
                leftIndent=20,
                rightIndent=30,
                spaceAfter=4,
                textColor=colors.HexColor('#0066cc')  # Blue for links
            ),
            'TOCEntry3': ParagraphStyle(
                'TOCEntry3',
                parent=styles['Normal'],
                fontName='Helvetica',
                fontSize=10,
                leftIndent=40,
                rightIndent=30,
                spaceAfter=3,
                textColor=colors.HexColor('#0066cc')  # Blue for links
            )
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
            self.styles['TOCEntry1'],
            self.styles['TOCEntry2'], 
            self.styles['TOCEntry3']
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
        if content.startswith('---'):
            try:
                end_index = content.index('---', 3)
                front_matter = content[3:end_index].strip()
                content = content[end_index + 3:].strip()
                
                # Parse front matter
                for line in front_matter.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        metadata[key.strip().lower()] = value.strip()
                
                self.logger.debug(f"Extracted metadata: {list(metadata.keys())}")
            except ValueError:
                self.logger.warning("No closing --- found for front matter")
        
        # Extract title from first H1 if not in metadata
        if metadata.get('title') == 'Document':
            title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            if title_match:
                metadata['title'] = title_match.group(1)
                self.logger.debug(f"Extracted title from H1: {metadata['title']}")
        
        return content, metadata
    
    def _create_heading_with_bookmark(self, text: str, style: ParagraphStyle, level: int):
        """Create a heading paragraph with TOC bookmark."""
        self.heading_counter += 1
        bookmark_name = f"heading_{self.heading_counter}"
        
        # Create the paragraph without HTML anchor (we'll use ReportLab bookmarks)
        para = Paragraph(text, style)
        
        # Add bookmark name for internal PDF navigation
        para._bookmarkName = bookmark_name
        
        # Add TOC entry information
        para.__toc_entry__ = (level, text, bookmark_name)
        
        self.logger.debug(f"Created heading: Level {level}, Text: {text}, Bookmark: {bookmark_name}")
        return para
    
    def _process_markdown_to_story(self, content: str, toc: TableOfContents = None) -> List:
        """Process markdown content and convert to ReportLab story elements."""
        self.logger.info("Processing markdown content to story elements")
        
        # Convert markdown to HTML
        md = markdown.Markdown(extensions=[
            'tables',
            'fenced_code',
            'footnotes',
            'attr_list',
            'def_list',
            'abbr',
            'toc',
            'nl2br',
            'sane_lists',
            'codehilite',
            'meta'
        ], extension_configs={
            'codehilite': {
                'css_class': 'highlight',
                'linenums': False,
                'guess_lang': True
            },
            'fenced_code': {
                'lang_prefix': 'language-'
            },
            'toc': {
                'permalink': False,
                'baselevel': 1
            }
        })
        
        html = md.convert(content)
        soup = BeautifulSoup(html, 'html.parser')
        
        story = []
        
        # Check if document has any headings
        headings = soup.find_all(['h1', 'h2', 'h3'])
        has_headings = bool(headings)
        self.logger.debug(f"Document has {len(headings)} headings")
        
        # If headings exist and TOC provided, add it
        if has_headings and toc:
            self.logger.info("Adding Table of Contents to document")
            story.append(Paragraph("Table of Contents", self.styles['TOCHeading']))
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
            if hasattr(element, 'name'):
                # Check if this is a manual TOC section to skip
                if element.name in ['h1', 'h2', 'h3']:
                    text = element.get_text().lower()
                    # Start skipping if we encounter a "table of contents" heading
                    if 'table of contents' in text and self._has_toc_section:
                        skip_manual_toc_section = True
                        continue
                    # Stop skipping once we hit the next major section
                    elif skip_manual_toc_section:
                        skip_manual_toc_section = False
                        # Don't skip this heading - process it normally
                
                # Skip list items that are part of a manual TOC
                if skip_manual_toc_section and element.name in ['ol', 'ul']:
                    continue
                
                # Process headings with TOC support
                if element.name == 'h1':
                    text = element.get_text()
                    para = self._create_heading_with_bookmark(text, self.styles['CustomHeading1'], 0)
                    story.append(para)
                    story.append(Spacer(1, 0.2*inch))
                    
                elif element.name == 'h2':
                    text = element.get_text()
                    para = self._create_heading_with_bookmark(text, self.styles['CustomHeading2'], 1)
                    story.append(para)
                    story.append(Spacer(1, 0.15*inch))
                    
                elif element.name == 'h3':
                    text = element.get_text()
                    para = self._create_heading_with_bookmark(text, self.styles['CustomHeading3'], 2)
                    story.append(para)
                    story.append(Spacer(1, 0.1*inch))
                
                elif element.name == 'p':
                    # Skip paragraphs containing images
                    if element.find('img'):
                        continue
                    
                    # Get paragraph text and clean HTML attributes
                    para_text = str(element)
                    
                    # Remove problematic attributes
                    para_text = re.sub(r'\s*id="[^"]*"', '', para_text)
                    para_text = re.sub(r'\s*class="[^"]*"', '', para_text)
                    
                    # Convert footnote references
                    para_text = re.sub(r'<sup[^>]*><a[^>]*>(\d+)</a></sup>', r'<sup>\1</sup>', para_text)
                    
                    # Check for code elements
                    if element.find('code'):
                        para_parts = []
                        parts = re.split(r'(<code>.*?</code>)', para_text)
                        code_count = 0
                        for part in parts:
                            if part.startswith('<code>') and part.endswith('</code>'):
                                code_count += 1
                                code_content = part[6:-7]
                                para_parts.append(f'<font name="Courier-Bold" size="10" color="#00c853">{code_content}</font>')
                            elif part:
                                para_parts.append(part)
                        
                        combined_text = ''.join(para_parts)
                        
                        # Use left alignment if multiple code elements
                        if code_count >= 2:
                            left_style = ParagraphStyle(
                                'TempLeft',
                                parent=self.styles['CustomBody'],
                                alignment=TA_LEFT
                            )
                            story.append(Paragraph(combined_text, left_style))
                        else:
                            story.append(Paragraph(combined_text, self.styles['CustomBody']))
                    else:
                        # Check paragraph length for justification
                        if len(para_text) < 150:
                            left_style = ParagraphStyle(
                                'TempLeft',
                                parent=self.styles['CustomBody'],
                                alignment=TA_LEFT
                            )
                            story.append(Paragraph(para_text, left_style))
                        else:
                            story.append(Paragraph(para_text, self.styles['CustomBody']))
                            
                elif element.name == 'pre':
                    # Code block processing
                    code_text = element.get_text().strip()
                    
                    code_elem = element.find('code')
                    if code_elem:
                        code_text = code_elem.get_text().strip()
                    
                    # Process code lines
                    lines = code_text.split('\n')
                    code_lines = []
                    for line in lines:
                        if line.strip():
                            line = line.replace('&', '&amp;')
                            line = line.replace('<', '&lt;')
                            line = line.replace('>', '&gt;')
                            code_lines.append(line)
                        else:
                            code_lines.append('')
                    
                    if code_lines:
                        code_content = '<br/>'.join(code_lines)
                        story.append(Paragraph(code_content, self.styles['CustomCode']))
                        story.append(Spacer(1, 0.1*inch))
                        
                elif element.name == 'div' and 'highlight' in element.get('class', []):
                    # Handle highlighted code blocks
                    code_elem = element.find('pre')
                    if code_elem:
                        code_text = code_elem.get_text().strip()
                        lines = code_text.split('\n')
                        code_lines = []
                        for line in lines:
                            if line.strip():
                                line = line.replace('&', '&amp;')
                                line = line.replace('<', '&lt;')
                                line = line.replace('>', '&gt;')
                                code_lines.append(line)
                            else:
                                code_lines.append('')
                        
                        if code_lines:
                            code_content = '<br/>'.join(code_lines)
                            story.append(Paragraph(code_content, self.styles['CustomCode']))
                            story.append(Spacer(1, 0.1*inch))
                            
                elif element.name == 'blockquote':
                    quote_text = element.get_text()
                    story.append(Paragraph(quote_text, self.styles['CustomQuote']))
                    story.append(Spacer(1, 0.1*inch))
                    
                elif element.name == 'ul' or element.name == 'ol':
                    for idx, li in enumerate(element.find_all('li', recursive=False), 1):
                        bullet = '• ' if element.name == 'ul' else f'{idx}. '
                        text = bullet + li.get_text()
                        story.append(Paragraph(text, self.styles['CustomBody']))
                    story.append(Spacer(1, 0.1*inch))
                    
                elif element.name == 'table':
                    # Process tables
                    table_data = []
                    for row in element.find_all('tr'):
                        row_data = []
                        for cell in row.find_all(['th', 'td']):
                            row_data.append(cell.get_text())
                        table_data.append(row_data)
                    
                    if table_data:
                        t = Table(table_data)
                        t.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f6f8fa')),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1a1a1a')),
                            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('FONTSIZE', (0, 0), (-1, 0), 10),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e1e4e8')),
                            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                            ('FONTSIZE', (0, 1), (-1, -1), 9),
                            ('PADDING', (0, 0), (-1, -1), 6),
                        ]))
                        story.append(t)
                        story.append(Spacer(1, 0.2*inch))
        
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
                    mask='auto'
                )
                logo_bottom = height - 2 * inch - img_height - 1.5 * inch
                self.logger.debug("Logo added to cover page")
            except Exception as e:
                self.logger.warning(f"Could not add logo: {e}")
        
        # Title
        title = metadata.get('title', 'Untitled Document')
        
        # Word wrap the title
        import textwrap
        title_font_size = 28
        char_width = title_font_size * 0.6
        max_chars = int(usable_width / char_width * 1.8)
        
        lines = textwrap.wrap(title, width=max_chars, break_long_words=False)
        
        # Check if we need smaller font
        use_smaller_font = False
        for line in lines:
            test_width = canvas_obj.stringWidth(line, 'Helvetica-Bold', title_font_size)
            if test_width > usable_width:
                use_smaller_font = True
                break
        
        if use_smaller_font:
            title_font_size = 24
        
        canvas_obj.setFont('Helvetica-Bold', title_font_size)
        canvas_obj.setFillColor(colors.HexColor('#1a1a1a'))
        
        # Draw title lines
        y_position = logo_bottom
        line_height = 0.4 * inch
        
        for line in lines:
            canvas_obj.drawCentredString(width / 2, y_position, line)
            y_position -= line_height
        
        # Subtitle if present
        if metadata.get('subtitle'):
            y_position -= 0.2 * inch
            canvas_obj.setFont('Helvetica', 16)
            canvas_obj.setFillColor(colors.HexColor('#666666'))
            subtitle_char_width = 16 * 0.5
            subtitle_max_chars = int(usable_width / subtitle_char_width * 1.8)
            subtitle_lines = textwrap.wrap(metadata['subtitle'], width=subtitle_max_chars)
            for line in subtitle_lines:
                canvas_obj.drawCentredString(width / 2, y_position, line)
                y_position -= 0.3 * inch
        
        # Author
        canvas_obj.setFont('Helvetica-Bold', 14)
        canvas_obj.setFillColor(colors.HexColor('#444444'))
        author_text = f"Prepared by {metadata.get('author', 'Unknown Author')}"
        author_width = canvas_obj.stringWidth(author_text, 'Helvetica-Bold', 14)
        if author_width > usable_width:
            author_lines = textwrap.wrap(author_text, width=int(usable_width / 14 * 2))
            y_pos = 3 * inch
            for line in author_lines:
                canvas_obj.drawCentredString(width / 2, y_pos, line)
                y_pos -= 0.25 * inch
        else:
            canvas_obj.drawCentredString(width / 2, 3 * inch, author_text)
        
        # Date
        canvas_obj.setFont('Helvetica', 11)
        canvas_obj.setFillColor(colors.HexColor('#888888'))
        canvas_obj.drawCentredString(width / 2, 1.5 * inch, metadata.get('date', datetime.now().strftime('%B %d, %Y')))
        
        # Version
        canvas_obj.setFont('Helvetica', 10)
        canvas_obj.setFillColor(colors.HexColor('#aaaaaa'))
        canvas_obj.drawCentredString(width / 2, 1 * inch, f"Version {metadata.get('version', '1.0.0')}")
        
        canvas_obj.restoreState()
    
    def _add_page_number(self, canvas_obj, doc):
        """Add page numbers and headers to each page."""
        canvas_obj.saveState()
        
        # Skip header/footer on first page
        if doc.page > 1:
            width, height = A4
            
            # Header - document title
            if hasattr(doc, 'metadata'):
                canvas_obj.setFont('Helvetica', 10)
                canvas_obj.setFillColor(colors.HexColor('#666666'))
                canvas_obj.drawCentredString(width / 2, height - 0.5 * inch, doc.metadata.get('title', ''))
            
            # Footer - page number
            canvas_obj.setFont('Helvetica', 9)
            canvas_obj.setFillColor(colors.HexColor('#666666'))
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
                        mask='auto'
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
        if str(input_path).startswith('To_Build/') or str(input_path).startswith('TO_Build/'):
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
        self.logger.info("="*60)
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
            with open(input_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract metadata
            content, metadata = self._extract_metadata(content)
            self.logger.info(f"Document title: {metadata.get('title', 'Untitled')}")
            
            # Generate output filename
            if output_file is None:
                base_name = input_path.stem
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                prefix = self.config.get('filename_prefix', '')
                output_file = f"{prefix}{base_name}_{timestamp}.pdf"
            
            output_path = self.output_dir / output_file
            self.logger.info(f"Output file: {output_path}")
            
            # Reset heading counter for new document
            self.heading_counter = 0
            
            # Create TOC for markdown files
            toc = None
            if input_path.suffix == '.md':
                toc = self._create_toc()
                self.logger.debug("Created TOC for markdown document")
            
            # Create PDF document with custom template for TOC support
            doc = TOCDocTemplate(
                str(output_path),
                pagesize=A4,
                rightMargin=self.config['margins']['right'] * mm,
                leftMargin=self.config['margins']['left'] * mm,
                topMargin=self.config['margins']['top'] * mm,
                bottomMargin=self.config['margins']['bottom'] * mm,
                title=metadata.get('title', 'Document'),
                author=metadata.get('author', 'Unknown'),
                subject=metadata.get('subject', ''),
                creator='GerdsenAI Document Builder',
                toc=toc  # Pass TOC to the document template
            )
            
            # Store metadata in doc
            doc.metadata = metadata
            
            # Build story
            story = []
            
            # Add cover page placeholder
            story.append(PageBreak())
            
            # Process content
            if input_path.suffix == '.md':
                content_story = self._process_markdown_to_story(content, toc)
                story.extend(content_story)
            else:
                # Plain text
                self.logger.debug("Processing plain text document")
                paragraphs = content.split('\n\n')
                for para in paragraphs:
                    if para.strip():
                        story.append(Paragraph(para.replace('\n', '<br/>'), self.styles['CustomBody']))
                        story.append(Spacer(1, 0.1*inch))
            
            # Build PDF with custom canvas for page tracking
            def make_canvas(*args, **kwargs):
                canv = NumberedCanvas(*args, **kwargs)
                canv.toc = toc
                return canv
            
            # Page handlers
            def on_every_page(canvas_obj, doc):
                if doc.page == 1:
                    self._create_cover_page(canvas_obj, doc, metadata)
                else:
                    self._add_page_number(canvas_obj, doc)
            
            # Build with custom canvas
            self.logger.info("Building PDF...")
            doc.multiBuild(story, canvasmaker=make_canvas, onFirstPage=on_every_page, onLaterPages=on_every_page)
            
            self.logger.info(f"✅ Successfully generated PDF: {output_path}")
            return str(output_path)
            
        except Exception as e:
            self.logger.error(f"❌ Error building document: {e}")
            self.logger.error(traceback.format_exc())
            raise
    
    def build_all_documents(self) -> List[str]:
        """Build all documents in the To_Build directory."""
        self.logger.info("="*60)
        self.logger.info("Building all documents")
        
        output_files = []
        success_count = 0
        error_count = 0
        
        # Get all markdown and text files
        files = list(self.to_build_dir.glob('*'))
        valid_files = [f for f in files if f.suffix in ['.md', '.txt']]
        
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
        self.logger.info("="*60)
        self.logger.info(f"Build Summary:")
        self.logger.info(f"  ✅ Successful: {success_count}")
        self.logger.info(f"  ❌ Failed: {error_count}")
        self.logger.info(f"  📄 Total: {len(valid_files)}")
        self.logger.info("="*60)
        
        return output_files


def main():
    """Main entry point for the document builder."""
    parser = argparse.ArgumentParser(
        description='GerdsenAI Document Builder - Convert Markdown/Text to Professional PDFs'
    )
    parser.add_argument(
        'input_file',
        nargs='?',
        help='Input file name (from To_Build directory). If not specified, builds all files.'
    )
    parser.add_argument(
        '-o', '--output',
        help='Output PDF file name'
    )
    parser.add_argument(
        '-a', '--all',
        action='store_true',
        help='Build all documents in To_Build directory'
    )
    parser.add_argument(
        '--repo-path',
        default='/Volumes/M2 Raid0/GerdsenAI_Repositories/GerdsenAI_Document_Builder',
        help='Repository path'
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
        logging.getLogger('DocumentBuilder').error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
