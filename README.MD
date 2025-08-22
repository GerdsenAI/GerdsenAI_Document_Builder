# 📚 GerdsenAI Document Builder

A world-class document builder that converts Markdown and text files into stunning, professional PDFs with custom styling, terminal-themed code blocks, and intelligent text formatting.

![GerdsenAI Logo](Assets/GerdsenAI_Neural_G_Invoice.png)

## ✨ Features

### 🎨 Professional Design
- **Custom Cover Pages** with logo, title, author, and metadata
- **SF Pro Font Support** for Apple-style typography (falls back to Helvetica if unavailable)
- **1-inch Margins** on all sides for professional printing
- **Page Numbers & Headers** on all pages except cover
- **Logo in Footer** for brand consistency

### 💻 Terminal-Style Code Formatting
- **Code Blocks**: Black background with bright green text (#00ff00) for authentic terminal appearance
- **Inline Code**: Bright green (#00c853) Courier-Bold font for visibility
- **Syntax Preservation**: Proper escaping of special characters
- **Multi-line Support**: Handles triple-backtick (```) markdown code blocks

### 📝 Intelligent Text Formatting
- **Smart Justification**: Automatically switches between justified and left-aligned text based on content
- **Dynamic Alignment Rules**:
  - Paragraphs with 2+ inline code snippets → Left aligned (prevents spacing issues)
  - Short paragraphs (<150 characters) → Left aligned
  - Long narrative text → Justified for professional appearance
- **Word Wrapping**: Proper handling of long technical terms
- **Hyphenation Support**: For better text distribution

### 🛠 Technical Features
- **Markdown Support**: Full markdown parsing with extensions (tables, footnotes, etc.)
- **Metadata Extraction**: YAML front matter support for document metadata
- **Table Formatting**: Professional table styling with alternating row colors
- **Blockquote Styling**: Distinctive formatting with blue accent border
- **Multiple Document Processing**: Build single or multiple documents at once
- **Configurable Filename Prefix**: Add custom prefixes to generated PDFs (default: `GerdsenAI_`)

## 📦 Installation

### Prerequisites
- macOS (tested on M1/M2)
- Python 3.9 or higher
- Homebrew (for font dependencies)

### Quick Setup

1. **Clone the repository**:
```bash
git clone https://github.com/yourusername/GerdsenAI_Document_Builder.git
cd GerdsenAI_Document_Builder
```

2. **Run the quick setup script**:
```bash
./quick_setup.sh
```

This will:
- Create a Python virtual environment
- Install all required packages (ReportLab, Markdown, BeautifulSoup4, etc.)
- Set up the directory structure
- Make the build script executable

### Manual Setup

If you prefer manual installation:

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## 📁 Repository Structure

```
GerdsenAI_Document_Builder/
├── To_Build/              # Place your .md or .txt files here
├── PDFs/                  # Generated PDFs are saved here
├── Assets/                # Logo and cover images
│   └── GerdsenAI_Neural_G_Invoice.png
├── SF Pro/                # SF Pro font files (optional)
│   ├── SF-Pro-Rounded-Regular.otf
│   ├── SF-Pro-Rounded-Bold.otf
│   └── ...
├── document_builder_reportlab.py  # Main document builder
├── build_document.sh      # Shell script for easy building
├── config.yaml           # Default configuration
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## 🚀 Usage

### Building Documents

1. **Place your markdown files** in the `To_Build` folder

2. **Build a specific document**:
```bash
./build_document.sh your_document.md
```

3. **Build all documents**:
```bash
./build_document.sh
```

4. **List available documents**:
```bash
./build_document.sh --list
```

### Document Format

#### Markdown with YAML Front Matter
```markdown
---
title: Your Document Title
author: Your Name
date: August 22, 2025
version: 1.0.0
---

# Introduction

Your content here with **bold**, *italic*, and `inline code`.

## Code Example

```python
def hello_world():
    print("Hello, World!")
```

## Features

- Bullet points
- With smart formatting
- And proper spacing
```

### Configuration

Edit `config.yaml` to customize default settings:

```yaml
default:
  author: "Your Name"
  company: "Your Company"
  version: "1.0.0"
  filename_prefix: "GerdsenAI_"  # Prefix for generated PDFs

margins:
  top: 25      # mm
  right: 20    # mm
  bottom: 25   # mm
  left: 20     # mm
```

#### Filename Prefix
The `filename_prefix` setting adds a custom prefix to all generated PDFs:
- Default: `GerdsenAI_`
- Example output: `GerdsenAI_document_20250822_123456.pdf`
- Set to empty string (`""`) to disable prefix

## 🎨 Styling Features

### Code Blocks
- **Terminal Theme**: Black background (#000000) with bright green text (#00ff00)
- **Border**: Dark gray (#333333) for definition
- **Padding**: 8pt for comfortable reading
- **Font**: Courier monospace for authenticity

### Inline Code
- **Color**: Bright green (#00c853)
- **Font**: Courier-Bold for emphasis
- **Size**: 10pt for visibility

### Text Alignment Logic
The document builder intelligently decides text alignment:

| Content Type | Alignment | Reason |
|-------------|-----------|---------|
| Long paragraphs (>150 chars) | Justified | Professional appearance |
| Short paragraphs (<150 chars) | Left | Prevents excessive spacing |
| Paragraphs with 2+ code snippets | Left | Avoids justification gaps |
| Headers | Left | Standard formatting |
| Code blocks | Left | Preserves formatting |

## 🔧 Advanced Features

### Custom Fonts
The builder supports SF Pro fonts but falls back gracefully to system fonts:
1. **Primary**: SF Pro Rounded (if available)
2. **Fallback**: Helvetica, Arial, sans-serif

### Metadata Support
Documents can include metadata in YAML front matter:
- `title`: Document title (shown on cover and headers)
- `author`: Author name
- `date`: Publication date
- `version`: Document version
- `subtitle`: Optional subtitle for cover page

### Page Layout
- **Cover Page**: Automatically generated with logo and metadata
- **Headers**: Document title on all pages except cover
- **Footers**: Page numbers and centered logo
- **Margins**: 1 inch on all sides for professional printing

## 🐛 Troubleshooting

### Font Warnings
If you see warnings about SF Pro fonts:
- These are optional - the document will still build correctly
- Uses Helvetica as fallback
- To use SF Pro, ensure .otf files are in the SF Pro directory

### Permission Issues
If you encounter permission errors:
```bash
chmod +x build_document.sh
chmod +x quick_setup.sh
```

### Missing Dependencies
If packages are missing:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

## 📋 Requirements

### Python Packages
- `reportlab>=4.0.0` - PDF generation
- `markdown>=3.5.0` - Markdown parsing
- `beautifulsoup4>=4.12.0` - HTML processing
- `Pillow>=10.0.0` - Image handling
- `pyyaml>=6.0` - YAML configuration

### System Requirements
- Python 3.9+
- macOS (tested) or Linux
- ~100MB disk space

## 🎯 Key Features Explained

### Smart Justification
The builder analyzes each paragraph to determine optimal alignment:
- Detects inline code frequency
- Measures paragraph length
- Prevents awkward spacing in technical content

### Terminal-Style Code
All code blocks and inline code use a terminal-inspired color scheme:
- Enhances readability
- Creates visual distinction
- Professional technical documentation appearance

### Professional Cover Pages
Automatic cover page generation with:
- Company logo
- Document title with word wrapping
- Author and date information
- Version tracking

## 📝 License

MIT License - Feel free to use and modify for your needs.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 👤 Author

**GerdsenAI**

## 🙏 Acknowledgments

- ReportLab for powerful PDF generation
- Python Markdown for excellent parsing
- The open-source community

---

**Note**: Place your markdown files in the `To_Build` folder and run `./build_document.sh` to generate professional PDFs with terminal-style code formatting and intelligent text alignment.
