# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Building Documents
- **Build specific document**: `./build_document.sh <filename.md>` - Converts a specific markdown file from To_Build/ to PDF
- **Build all documents**: `./build_document.sh --all` or `./build_document.sh` - Processes all files in To_Build/
- **Setup environment**: `./build_document.sh --setup` - Creates venv and installs dependencies
- **Clean PDFs**: `./build_document.sh --clean` - Removes all PDFs from output directory
- **Show help**: `./build_document.sh --help` - Display available options

### Python Development
- **Activate virtual environment**: `source venv/bin/activate`
- **Run script directly**: `python document_builder_reportlab.py [options]`
- **Install/update dependencies**: `pip install -r requirements.txt`

### Testing
- **Test document generation**: Place a markdown file in `To_Build/` and run `./build_document.sh <filename>`
- **Verify PDF output**: Check `PDFs/` directory for generated files with timestamp

## Architecture

### Core Components

**DocumentBuilder Class** (`document_builder_reportlab.py`)
Main class that orchestrates the document conversion pipeline:
- Loads configuration from `config.yaml`
- Registers fonts (SF Pro with Helvetica fallback)
- Parses markdown with extensions (tables, code blocks, TOC)
- Generates professional PDFs with ReportLab

### Key Processing Pipeline
1. **Input Processing**: Reads markdown/text from `To_Build/`
2. **Metadata Extraction**: Parses YAML front matter for title, author, date
3. **Markdown Parsing**: Converts to HTML using Python-Markdown with extensions
4. **HTML to PDF**: Transforms parsed content to ReportLab flowables
5. **Style Application**: Applies custom styles (fonts, colors, spacing)
6. **PDF Generation**: Creates final document with cover page, TOC, headers/footers

### Styling System

**Code Formatting**
- Terminal-style blocks: Black background (#000000), bright green text (#00ff00)
- Inline code: Bright green (#00c853), Courier-Bold font
- Preserves formatting and escapes special characters

**Text Justification Logic**
Smart alignment based on content analysis:
- Paragraphs with 2+ code snippets → Left aligned
- Short paragraphs (<150 chars) → Left aligned  
- Long narrative text → Justified
- Headers/code blocks → Always left aligned

### Configuration Structure

**config.yaml** defines:
- Default metadata (author, company, version)
- Page settings (size, margins, orientation)
- Typography (font families, sizes, weights)
- Colors (primary, code, links, tables)
- Export options (optimization, compression)

**Filename prefix**: Set in config as `filename_prefix` (default: "GerdsenAI_")

### Directory Layout
- `To_Build/`: Place input markdown files here
- `PDFs/`: Generated PDFs saved here with timestamp
- `Assets/`: Logo and cover images (GerdsenAI_Neural_G_Invoice.png)
- `SF Pro/`: Optional font files (.otf format)
- `venv/`: Python virtual environment (auto-created)