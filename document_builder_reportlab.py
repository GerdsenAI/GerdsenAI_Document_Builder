#!/usr/bin/env python3
"""
GerdsenAI Document Builder
A world-class document builder that converts Markdown/Text files to professional PDFs
with custom styling, Mermaid diagram support, and SF Pro font integration.
"""

import os
import sys
import argparse
import re
import base64
import tempfile
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
import io

# Third-party imports
import markdown
from markdown.extensions import tables, fenced_code, footnotes, attr_list, def_list, abbr, toc
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
from reportlab.platypus import Table, TableStyle, PageBreak, KeepTogether
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image
from bs4 import BeautifulSoup
import yaml


class DocumentBuilder:
    """Main document builder class for converting Markdown/Text to PDF."""
    
    def __init__(self, repo_path: str):
        """Initialize the document builder with repository path."""
        self.repo_path = Path(repo_path)
        self.to_build_dir = self.repo_path / "To_Build"
        self.assets_dir = self.repo_path / "Assets"
        self.fonts_dir = self.repo_path / "SF Pro"
        self.output_dir = self.repo_path / "PDFs"
        
        # Ensure output directory exists
        self.output_dir.mkdir(exist_ok=True)
        
        # Load configuration
        self.config = self._load_config()
        
        # Register fonts
        self._register_fonts()
        
        # Setup styles
        self.styles = self._setup_styles()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from config.yaml or use defaults."""
        config_path = self.repo_path / "config.yaml"
        
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
            "footer_height": 15
        }
        
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    yaml_config = yaml.safe_load(f)
                    if yaml_config and 'default' in yaml_config:
                        default_config.update(yaml_config['default'])
                    if 'margins' in yaml_config:
                        default_config['margins'] = yaml_config['margins']
            except Exception as e:
                print(f"Warning: Could not load config.yaml: {e}")
        
        return default_config
    
    def _register_fonts(self):
        """Register SF Pro fonts with ReportLab."""
        font_mappings = {
            'SFPro': 'SF-Pro-Rounded-Regular.otf',
            'SFPro-Bold': 'SF-Pro-Rounded-Bold.otf',
            'SFPro-Light': 'SF-Pro-Rounded-Light.otf',
            'SFPro-Medium': 'SF-Pro-Rounded-Medium.otf',
            'SFPro-Semibold': 'SF-Pro-Rounded-Semibold.otf',
            'SFPro-Heavy': 'SF-Pro-Rounded-Heavy.otf',
            'SFPro-Black': 'SF-Pro-Rounded-Black.otf',
        }
        
        for font_name, font_file in font_mappings.items():
            font_path = self.fonts_dir / font_file
            if font_path.exists():
                try:
                    pdfmetrics.registerFont(TTFont(font_name, str(font_path)))
                except Exception as e:
                    print(f"Warning: Could not register font {font_name}: {e}")
    
    def _setup_styles(self) -> Dict[str, ParagraphStyle]:
        """Setup paragraph styles for the document."""
        styles = getSampleStyleSheet()
        
        # Custom styles with SF Pro font
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
                wordWrap='LTR',  # Left-to-right word wrapping
                splitLongWords=1,  # Allow splitting long words
                bulletIndent=0,
                leftIndent=0,
                rightIndent=0
            ),
            'CustomCode': ParagraphStyle(
                'CustomCode',
                parent=styles['Code'],
                fontName='Courier',
                fontSize=9,
                textColor=colors.HexColor('#00ff00'),  # Bright green text
                backColor=colors.HexColor('#000000'),  # Black background
                borderColor=colors.HexColor('#333333'),  # Dark gray border
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
                textColor=colors.HexColor('#00c853'),  # Bright terminal green
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
            )
        }
        
        # Add custom styles to the style sheet
        for name, style in custom_styles.items():
            styles.add(style)
        
        return styles
    
    def _extract_metadata(self, content: str) -> Tuple[str, Dict[str, str]]:
        """Extract metadata from markdown front matter if present."""
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
            except ValueError:
                pass  # No closing --- found
        
        # Extract title from first H1 if not in metadata
        if metadata.get('title') == 'Document':
            title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            if title_match:
                metadata['title'] = title_match.group(1)
        
        return content, metadata
    
    def _process_markdown_to_story(self, content: str) -> List:
        """Process markdown content and convert to ReportLab story elements."""
        # Convert markdown to HTML
        md = markdown.Markdown(extensions=[
            'tables',
            'fenced_code',  # This should handle ``` blocks
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
            }
        })
        
        html = md.convert(content)
        soup = BeautifulSoup(html, 'html.parser')
        
        story = []
        
        # Process HTML elements
        for element in soup.children:
            if element.name == 'h1':
                story.append(Paragraph(element.get_text(), self.styles['CustomHeading1']))
                story.append(Spacer(1, 0.2*inch))
            elif element.name == 'h2':
                story.append(Paragraph(element.get_text(), self.styles['CustomHeading2']))
                story.append(Spacer(1, 0.15*inch))
            elif element.name == 'h3':
                story.append(Paragraph(element.get_text(), self.styles['CustomHeading3']))
                story.append(Spacer(1, 0.1*inch))
            elif element.name == 'p':
                # Check if paragraph contains images - handle them separately
                if element.find('img'):
                    # Skip paragraphs containing images for now
                    # Images should be handled as separate elements, not inline
                    continue
                # Check if paragraph contains code elements
                elif element.find('code'):
                    # Process each part of the paragraph
                    para_parts = []
                    text = str(element)
                    # Split by code tags and process
                    parts = re.split(r'(<code>.*?</code>)', text)
                    code_count = 0
                    for part in parts:
                        if part.startswith('<code>') and part.endswith('</code>'):
                            code_count += 1
                            # Extract code content
                            code_content = part[6:-7]  # Remove <code> and </code>
                            # Create inline code with terminal-like green color on dark background effect
                            # Using Courier-Bold and bright green to simulate terminal
                            para_parts.append(f'<font name="Courier-Bold" size="10" color="#00c853">{code_content}</font>')
                        elif part:
                            para_parts.append(part)
                    
                    combined_text = ''.join(para_parts)
                    
                    # Use left alignment if paragraph has many code elements to avoid bad spacing
                    # Changed threshold from 3 to 2 for better handling
                    if code_count >= 2:  # If 2 or more code snippets, use left align
                        # Create a copy of the body style with left alignment
                        left_style = ParagraphStyle(
                            'TempLeft',
                            parent=self.styles['CustomBody'],
                            alignment=TA_LEFT
                        )
                        story.append(Paragraph(combined_text, left_style))
                    else:
                        story.append(Paragraph(combined_text, self.styles['CustomBody']))
                else:
                    # Check if paragraph is short (might cause bad justification)
                    para_text = str(element)
                    if len(para_text) < 150:  # Short paragraphs look bad justified
                        left_style = ParagraphStyle(
                            'TempLeft',
                            parent=self.styles['CustomBody'],
                            alignment=TA_LEFT
                        )
                        story.append(Paragraph(para_text, left_style))
                    else:
                        story.append(Paragraph(para_text, self.styles['CustomBody']))
            elif element.name == 'pre':
                # Code block with terminal styling
                code_text = element.get_text().strip()
                
                # Check if this is actually a code block or just preformatted text
                # Look for code tag inside pre or div with highlight class
                code_elem = element.find('code')
                if code_elem:
                    code_text = code_elem.get_text().strip()
                
                # Create terminal-style code block
                # Split long code blocks into smaller chunks to avoid page breaks
                lines = code_text.split('\n')
                
                # Add the code block with proper styling
                code_lines = []
                for line in lines:
                    if line.strip():  # Skip empty lines
                        # Escape XML characters
                        line = line.replace('&', '&amp;')
                        line = line.replace('<', '&lt;')
                        line = line.replace('>', '&gt;')
                        code_lines.append(line)
                    else:
                        code_lines.append('')  # Keep empty lines for spacing
                
                # Join lines and create paragraph with code style
                if code_lines:
                    code_content = '<br/>'.join(code_lines)
                    story.append(Paragraph(code_content, self.styles['CustomCode']))
                    story.append(Spacer(1, 0.1*inch))
            elif element.name == 'div' and 'highlight' in element.get('class', []):
                # Handle highlighted code blocks from codehilite
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
                for li in element.find_all('li', recursive=False):
                    bullet = '• ' if element.name == 'ul' else f'{li.sourceline}. '
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
        
        return story
    
    def _create_cover_page(self, canvas_obj, doc, metadata: Dict[str, str]):
        """Create a cover page for the document."""
        canvas_obj.saveState()
        
        # Set page size
        width, height = A4
        
        # Define margins (1 inch = 72 points)
        margin = 1 * inch  # 1 inch margins on all sides
        usable_width = width - (2 * margin)
        
        # Add logo if exists
        logo_path = self.assets_dir / "GerdsenAI_Neural_G_Invoice.png"
        logo_bottom = height - 3.5 * inch  # Position where logo ends
        
        if logo_path.exists():
            try:
                img = Image.open(logo_path)
                aspect = img.height / img.width
                img_width = 2.5 * inch  # Smaller logo
                img_height = img_width * aspect
                # Center the logo
                canvas_obj.drawImage(
                    str(logo_path),
                    (width - img_width) / 2,
                    height - 2 * inch - img_height,
                    width=img_width,
                    height=img_height,
                    preserveAspectRatio=True,
                    mask='auto'
                )
                logo_bottom = height - 2 * inch - img_height - 1.5 * inch  # Added more space (1.5 inches)
            except Exception as e:
                print(f"Warning: Could not add logo: {e}")
        
        # Title - positioned below the logo with proper wrapping
        title = metadata.get('title', 'Untitled Document')
        
        # Calculate maximum characters per line based on font size and usable width
        # Using a more accurate calculation for Helvetica-Bold at 28pt
        # Approximate character width is about 0.6 of font size for Helvetica-Bold
        title_font_size = 28
        char_width = title_font_size * 0.6  # in points
        max_chars = int(usable_width / char_width * 1.8)  # Adjusted multiplier for better fit
        
        # Word wrap the title within the margins
        import textwrap
        lines = textwrap.wrap(title, width=max_chars, break_long_words=False)
        
        # Determine if we need to use a smaller font for all lines to maintain consistency
        use_smaller_font = False
        for line in lines:
            test_width = canvas_obj.stringWidth(line, 'Helvetica-Bold', title_font_size)
            if test_width > usable_width:
                use_smaller_font = True
                break
        
        # Set consistent font size for all title lines
        if use_smaller_font:
            title_font_size = 24
        
        canvas_obj.setFont('Helvetica-Bold', title_font_size)
        canvas_obj.setFillColor(colors.HexColor('#1a1a1a'))
        
        # Start title below logo
        y_position = logo_bottom
        line_height = 0.4 * inch
        
        # Draw all title lines with the same font size
        for line in lines:
            canvas_obj.drawCentredString(width / 2, y_position, line)
            y_position -= line_height
        
        # Subtitle if present
        if metadata.get('subtitle'):
            y_position -= 0.2 * inch  # Extra space before subtitle
            canvas_obj.setFont('Helvetica', 16)
            canvas_obj.setFillColor(colors.HexColor('#666666'))
            # Calculate max chars for subtitle
            subtitle_char_width = 16 * 0.5
            subtitle_max_chars = int(usable_width / subtitle_char_width * 1.8)
            subtitle_lines = textwrap.wrap(metadata['subtitle'], width=subtitle_max_chars)
            for line in subtitle_lines:
                canvas_obj.drawCentredString(width / 2, y_position, line)
                y_position -= 0.3 * inch
        
        # Author - centered in lower portion
        canvas_obj.setFont('Helvetica-Bold', 14)
        canvas_obj.setFillColor(colors.HexColor('#444444'))
        author_text = f"Prepared by {metadata.get('author', 'Unknown Author')}"
        # Check if author text fits within margins
        author_width = canvas_obj.stringWidth(author_text, 'Helvetica-Bold', 14)
        if author_width > usable_width:
            # Wrap author text if needed
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
    
    def build_document(self, input_file: str, output_file: Optional[str] = None) -> str:
        """Build a PDF document from input file."""
        input_path = self.to_build_dir / input_file
        
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        # Read content
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract metadata
        content, metadata = self._extract_metadata(content)
        
        # Generate output filename
        if output_file is None:
            base_name = input_path.stem
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            # Use filename prefix from config, default to empty string if not set
            prefix = self.config.get('filename_prefix', '')
            output_file = f"{prefix}{base_name}_{timestamp}.pdf"
        
        output_path = self.output_dir / output_file
        
        # Create PDF document
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            rightMargin=self.config['margins']['right'] * mm,
            leftMargin=self.config['margins']['left'] * mm,
            topMargin=self.config['margins']['top'] * mm,
            bottomMargin=self.config['margins']['bottom'] * mm,
            title=metadata.get('title', 'Document'),
            author=metadata.get('author', 'Unknown'),
            subject=metadata.get('subject', ''),
            creator='GerdsenAI Document Builder'
        )
        
        # Store metadata in doc for access in callbacks
        doc.metadata = metadata
        
        # Build story
        story = []
        
        # Add cover page
        story.append(PageBreak())
        
        # Process content
        if input_path.suffix == '.md':
            content_story = self._process_markdown_to_story(content)
            story.extend(content_story)
        else:
            # Plain text
            paragraphs = content.split('\n\n')
            for para in paragraphs:
                if para.strip():
                    story.append(Paragraph(para.replace('\n', '<br/>'), self.styles['CustomBody']))
                    story.append(Spacer(1, 0.1*inch))
        
        # Build PDF with custom canvas
        def on_every_page(canvas_obj, doc):
            if doc.page == 1:
                self._create_cover_page(canvas_obj, doc, metadata)
            else:
                self._add_page_number(canvas_obj, doc)
        
        doc.build(story, onFirstPage=on_every_page, onLaterPages=on_every_page)
        
        print(f"✅ Successfully generated PDF: {output_path}")
        return str(output_path)
    
    def build_all_documents(self) -> List[str]:
        """Build all documents in the To_Build directory."""
        output_files = []
        
        # Get all markdown and text files
        for file_path in self.to_build_dir.glob('*'):
            if file_path.suffix in ['.md', '.txt']:
                try:
                    print(f"📄 Building: {file_path.name}")
                    output = self.build_document(file_path.name)
                    output_files.append(output)
                except Exception as e:
                    print(f"❌ Error building {file_path.name}: {e}")
                    import traceback
                    traceback.print_exc()
        
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
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
