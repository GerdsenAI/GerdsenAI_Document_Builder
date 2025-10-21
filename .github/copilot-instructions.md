# GerdsenAI Document Builder - AI Agent Instructions

## Architecture Overview

This is a **professional PDF document builder** that converts Markdown/text files into high-quality PDFs with custom styling. The system is built around a single `DocumentBuilder` class in `document_builder_reportlab.py` that orchestrates the entire markdown → HTML → PDF pipeline using ReportLab.

### Core Components

- **DocumentBuilder class**: Main orchestrator handling the complete build pipeline
- **TOCDocTemplate & NumberedCanvas**: Custom ReportLab classes for Table of Contents and page numbering
- **Markdown Extensions**: Uses Python-Markdown with extensions for tables, code highlighting, footnotes
- **Mermaid Integration**: Local rendering via Playwright/Chromium (not API-based)
- **Smart Text Alignment**: Automatically switches between justified/left-aligned based on content analysis

## Project Structure & Conventions

```
To_Build/           # Input: Place markdown/text files here
PDFs/              # Output: Generated PDFs land here
Assets/            # Logo/images for cover pages
SF Pro/            # Optional Apple fonts (fallback to system fonts)
Logs/              # Comprehensive build logs with rotation
config.yaml        # Central configuration (NOT command-line args)
```

**Key Convention**: The system uses `config.yaml` for ALL configuration. Avoid adding command-line options - extend the YAML schema instead.

## Development Workflows

### Building Documents

```bash
# Activate venv first (ALWAYS)
source venv/bin/activate

# Build single document
python document_builder_reportlab.py filename.md

# Build all documents in To_Build/
python document_builder_reportlab.py --all

# Using shell wrapper (macOS/Linux)
./build_document.sh filename.md
./build_document.sh --all
```

### Testing New Features

1. **Use TabX files**: `To_Build/TabX_*_Flows.md` contain 20+ Mermaid diagrams for testing
2. **Check logs**: Always examine `Logs/document_builder_YYYYMMDD.log` for detailed execution flow
3. **Test font fallback**: Remove `SF Pro/` directory to test system font fallback behavior

### Debugging Pipeline Issues

The build pipeline follows this exact order:

1. **Input resolution** → `_resolve_input_path()` handles various path formats
2. **Metadata extraction** → YAML front matter parsed via `_extract_metadata()`
3. **Markdown → HTML** → Python-Markdown with custom extensions
4. **HTML → ReportLab Story** → `_process_markdown_to_story()` converts to PDF elements
5. **PDF generation** → Custom TOCDocTemplate with NumberedCanvas for page tracking

## Code Patterns & Conventions

### Logging Pattern

```python
self.logger.info("=" * 60)  # Section separators
self.logger.info("Building document: {filename}")
self.logger.debug(f"Processing {len(elements)} elements")  # Detailed info
self.logger.error(f"❌ Error: {error}")  # User-facing errors
```

### Error Handling Pattern

```python
try:
    # Main logic
except Exception as e:
    self.logger.error(f"❌ Error: {e}")
    self.logger.error(traceback.format_exc())  # Full stack trace to logs
    raise  # Re-raise for caller
```

### Style Configuration

Styles are created once in `_setup_styles()` and reused. Follow the existing pattern:

- `CustomBody` for main text with smart justification logic
- `CodeBlock` for terminal-style code (black bg, green text)
- `TOCEntry1/2/3` for table of contents levels

### Mermaid Integration Details

- **Detection**: HTML `<code class="language-mermaid">` elements
- **Rendering**: Temporary `.mmd` files → Playwright → PNG → ReportLab Image
- **Fallback**: Invalid diagrams become code blocks (graceful degradation)
- **Config**: All settings in `config.yaml` under `mermaid:` section

## Common Modification Patterns

### Adding New Markdown Extensions

```python
# In _process_markdown_to_story()
md = markdown.Markdown(extensions=[
    'tables', 'fenced_code', 'footnotes',
    'your_new_extension'  # Add here
], extension_configs={
    'your_new_extension': {
        'option': 'value'
    }
})
```

### Adding New PDF Elements

```python
# In _process_markdown_to_story(), add new elif branch
elif element.name == 'your_element':
    # Convert to ReportLab element
    story.append(YourReportLabElement(...))
```

### Extending Configuration

```yaml
# In config.yaml - prefer nested structure
your_feature:
  enabled: true
  options:
    setting1: value1
    setting2: value2
```

## Integration Points

### Font System

- **Primary**: SF Pro fonts from `SF Pro/` directory
- **Registration**: `_register_fonts()` with TTFont, includes error handling
- **Fallback**: Helvetica → Arial → Sans-serif (automatic)

### Image Processing

- **Cover logos**: `Assets/` directory, PIL for resizing/processing
- **Mermaid diagrams**: Temporary PNG files, auto-cleanup
- **Scaling**: Respects page margins and `max_width_percent` config

### Build Script Integration

`build_document.sh` provides environment management:

- Virtual environment activation
- Dependency installation
- Directory structure creation
- Batch processing with error counts

## Performance Considerations

- **Mermaid overhead**: ~0.5s per diagram after Chromium startup
- **Font loading**: One-time cost per build session
- **Memory usage**: ~50-200MB depending on document complexity
- **Batch processing**: More efficient than individual builds

## Testing Strategy

Use the provided test documents:

- `TabX_React_Native_Flows.md`: Large document with multiple Mermaid diagrams
- `TabX_Figma_Flows.md`: Tests various diagram types and styling

Monitor logs for performance metrics and error patterns during development.
