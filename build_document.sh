#!/bin/bash

################################################################################
# GerdsenAI Document Builder
# A world-class document conversion tool for macOS
################################################################################

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Configuration
REPO_PATH="/Volumes/M2 Raid0/GerdsenAI_Repositories/GerdsenAI_Document_Builder"
PYTHON_SCRIPT="$REPO_PATH/document_builder_reportlab.py"
VENV_PATH="$REPO_PATH/venv"

# Banner
print_banner() {
    echo -e "${CYAN}${BOLD}"
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║                                                                ║"
    echo "║           🚀 GerdsenAI Document Builder v1.0.0 🚀              ║"
    echo "║                                                                ║"
    echo "║         World-Class Markdown to PDF Conversion Tool           ║"
    echo "║                                                                ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Help message
show_help() {
    echo -e "${BOLD}Usage:${NC}"
    echo "  $0 [OPTIONS] [FILENAME]"
    echo ""
    echo -e "${BOLD}Options:${NC}"
    echo "  -h, --help           Show this help message"
    echo "  -a, --all            Build all documents in To_Build folder"
    echo "  -o, --output FILE    Specify output PDF filename"
    echo "  -s, --setup          Install/update dependencies"
    echo "  -l, --list           List all available documents"
    echo "  -c, --clean          Clean output directory"
    echo "  -w, --watch          Watch for changes and auto-build"
    echo ""
    echo -e "${BOLD}Examples:${NC}"
    echo "  $0                           # Build all documents"
    echo "  $0 document.md               # Build specific document"
    echo "  $0 -o report.pdf doc.md      # Build with custom output name"
    echo "  $0 --setup                   # Setup environment"
    echo ""
}

# Setup Python environment
setup_environment() {
    echo -e "${YELLOW}📦 Setting up Python environment...${NC}"
    
    # Check if Python 3 is installed
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python 3 is not installed. Please install Python 3.8 or later.${NC}"
        exit 1
    fi
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "$VENV_PATH" ]; then
        echo -e "${BLUE}Creating virtual environment...${NC}"
        python3 -m venv "$VENV_PATH"
    fi
    
    # Activate virtual environment
    source "$VENV_PATH/bin/activate"
    
    # Upgrade pip
    echo -e "${BLUE}Upgrading pip...${NC}"
    pip install --upgrade pip > /dev/null 2>&1
    
    # Install required packages
    echo -e "${BLUE}Installing required packages...${NC}"
    pip install --upgrade \
        markdown \
        weasyprint \
        pillow \
        beautifulsoup4 \
        pymupdf \
        watchdog \
        pygments \
        pyyaml > /dev/null 2>&1
    
    # Check for mermaid-cli
    if ! command -v mmdc &> /dev/null; then
        echo -e "${YELLOW}⚠️  Mermaid CLI not found. To enable Mermaid diagram support:${NC}"
        echo -e "${CYAN}   npm install -g @mermaid-js/mermaid-cli${NC}"
    fi
    
    echo -e "${GREEN}✅ Environment setup complete!${NC}"
}

# List available documents
list_documents() {
    echo -e "${BOLD}📄 Available documents in To_Build:${NC}"
    echo ""
    
    if [ -d "$REPO_PATH/To_Build" ]; then
        # Use find instead of bash glob expansion
        found_files=false
        while IFS= read -r file; do
            if [ -f "$file" ]; then
                found_files=true
                filename=$(basename "$file")
                size=$(du -h "$file" | cut -f1)
                echo -e "  ${CYAN}•${NC} $filename ${YELLOW}($size)${NC}"
            fi
        done < <(find "$REPO_PATH/To_Build" -maxdepth 1 \( -name "*.md" -o -name "*.txt" \) 2>/dev/null)
        
        if [ "$found_files" = false ]; then
            echo -e "  ${YELLOW}No documents found${NC}"
        fi
    else
        echo -e "${RED}To_Build directory not found!${NC}"
    fi
    echo ""
}

# Clean output directory
clean_output() {
    echo -e "${YELLOW}🧹 Cleaning output directory...${NC}"
    
    if [ -d "$REPO_PATH/PDFs" ]; then
        count=$(find "$REPO_PATH/PDFs" -name "*.pdf" 2>/dev/null | wc -l | tr -d ' ')
        if [ "$count" -gt 0 ]; then
            echo -e "${BLUE}Found $count PDF file(s)${NC}"
            read -p "Are you sure you want to delete all PDFs? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                rm -f "$REPO_PATH/PDFs"/*.pdf
                echo -e "${GREEN}✅ Cleaned $count file(s)${NC}"
            else
                echo -e "${YELLOW}Cancelled${NC}"
            fi
        else
            echo -e "${BLUE}No PDF files to clean${NC}"
        fi
    fi
}

# Watch for changes
watch_mode() {
    echo -e "${CYAN}👀 Watching for changes in To_Build directory...${NC}"
    echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
    echo ""
    
    # Python script for watching
    "$VENV_PATH/bin/python3" << 'EOF'
import time
import os
import sys
import subprocess
from pathlib import Path

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    print("❌ Error: watchdog not installed. Please run setup first.")
    sys.exit(1)

class DocumentHandler(FileSystemEventHandler):
    def __init__(self, repo_path):
        self.repo_path = repo_path
        self.last_build = {}
    
    def on_modified(self, event):
        if not event.is_directory:
            file_path = Path(event.src_path)
            if file_path.suffix in ['.md', '.txt']:
                # Debounce - don't rebuild too quickly
                current_time = time.time()
                last_time = self.last_build.get(file_path.name, 0)
                if current_time - last_time > 2:  # 2 second debounce
                    self.last_build[file_path.name] = current_time
                    print(f"\n🔄 Change detected: {file_path.name}")
                    print(f"📝 Rebuilding...")
                    try:
                        result = subprocess.run(
                            [f'{self.repo_path}/venv/bin/python3', f'{self.repo_path}/document_builder_reportlab.py', file_path.name],
                            capture_output=True,
                            text=True
                        )
                        if result.returncode == 0:
                            print("✅ Build successful!")
                        else:
                            print(f"❌ Build failed: {result.stderr}")
                    except Exception as e:
                        print(f"❌ Error: {e}")

# Setup observer
repo_path = os.environ.get('REPO_PATH', '/Volumes/M2 Raid0/GerdsenAI_Repositories/GerdsenAI_Document_Builder')
to_build_path = os.path.join(repo_path, 'To_Build')

if os.path.exists(to_build_path):
    event_handler = DocumentHandler(repo_path)
    observer = Observer()
    observer.schedule(event_handler, to_build_path, recursive=False)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\n\n👋 Stopping watch mode...")
    observer.join()
else:
    print(f"❌ To_Build directory not found: {to_build_path}")
    sys.exit(1)
EOF
}

# Build documents
build_documents() {
    # Check if virtual environment exists
    if [ ! -d "$VENV_PATH" ]; then
        echo -e "${YELLOW}Virtual environment not found. Please run setup first.${NC}"
        echo -e "${CYAN}Run: ./quick_setup.sh${NC}"
        exit 1
    fi
    
    # Check if Python script exists
    if [ ! -f "$PYTHON_SCRIPT" ]; then
        echo -e "${RED}❌ Python script not found at: $PYTHON_SCRIPT${NC}"
        exit 1
    fi
    
    # Run the Python script with venv python
    "$VENV_PATH/bin/python3" "$PYTHON_SCRIPT" "$@"
}

# Main script logic
main() {
    print_banner
    
    # Parse command line arguments
    case "$1" in
        -h|--help)
            show_help
            ;;
        -s|--setup)
            setup_environment
            ;;
        -l|--list)
            list_documents
            ;;
        -c|--clean)
            clean_output
            ;;
        -w|--watch)
            if [ ! -d "$VENV_PATH" ]; then
                setup_environment
            fi
            watch_mode
            ;;
        -a|--all)
            echo -e "${CYAN}📚 Building all documents...${NC}"
            build_documents --all
            ;;
        -o|--output)
            if [ -z "$3" ]; then
                echo -e "${RED}❌ Please specify input file after output option${NC}"
                exit 1
            fi
            echo -e "${CYAN}📄 Building document with custom output...${NC}"
            build_documents -o "$2" "$3"
            ;;
        "")
            # No arguments - build all
            echo -e "${CYAN}📚 Building all documents...${NC}"
            build_documents --all
            ;;
        *)
            # Assume it's a filename
            echo -e "${CYAN}📄 Building document: $1${NC}"
            build_documents "$@"
            ;;
    esac
}

# Export REPO_PATH for Python watch script
export REPO_PATH

# Run main function
main "$@"
