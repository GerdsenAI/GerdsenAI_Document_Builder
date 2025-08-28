#!/bin/bash

# GerdsenAI Document Builder
# Consolidated build script with enhanced error handling and logging

# Get the directory of this script
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

# Colors
GREEN='[0;32m'
YELLOW='[1;33m'
RED='[0;31m'
BLUE='[0;34m'
NC='[0m'

# Create Logs directory if it doesn't exist
mkdir -p "$DIR/Logs"

echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║      🚀 GerdsenAI Document Builder v2.0.0 🚀            ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"
echo -e "${BLUE}Log files will be saved to: $DIR/Logs/${NC}"

# Function to setup environment
setup() {
    echo -e "${YELLOW}Setting up environment...${NC}"
    
    # Create necessary directories
    mkdir -p "$DIR/To_Build" "$DIR/PDFs" "$DIR/Assets" "$DIR/Logs"
    
    # Create venv if it doesn't exist
    if [ ! -d "venv" ]; then
        echo "Creating virtual environment..."
        python3 -m venv venv || {
            echo -e "${RED}❌ Failed to create virtual environment${NC}"
            exit 1
        }
    fi
    
    # Activate and install packages
    source venv/bin/activate || {
        echo -e "${RED}❌ Failed to activate virtual environment${NC}"
        exit 1
    }
    
    echo "Installing dependencies..."
    pip install --upgrade pip > /dev/null 2>&1
    pip install --upgrade markdown reportlab pillow beautifulsoup4 pyyaml watchdog pygments > /dev/null 2>&1 || {
        echo -e "${RED}❌ Failed to install dependencies${NC}"
        echo "Please check the log file for details"
        exit 1
    }
    
    echo -e "${GREEN}✅ Setup complete!${NC}"
}

# Function to build documents with error handling
build() {
    # Check if venv exists
    if [ ! -d "venv" ]; then
        echo -e "${YELLOW}Virtual environment not found. Setting up...${NC}"
        setup
    fi
    
    # Activate virtual environment
    source venv/bin/activate || {
        echo -e "${RED}❌ Failed to activate virtual environment${NC}"
        exit 1
    }
    
    # Check if document_builder_reportlab.py exists
    if [ ! -f "document_builder_reportlab.py" ]; then
        echo -e "${RED}❌ Error: document_builder_reportlab.py not found${NC}"
        exit 1
    fi
    
    # Run the document builder
    echo -e "${BLUE}Starting document build process...${NC}"
    python document_builder_reportlab.py "$@"
    
    # Check exit code
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Build process completed successfully${NC}"
        echo -e "${BLUE}Check the Logs directory for detailed build information${NC}"
    else
        echo -e "${RED}❌ Build process failed${NC}"
        echo -e "${YELLOW}Please check the log files in $DIR/Logs/ for details${NC}"
        exit 1
    fi
}

# Function to list available documents
list_documents() {
    echo -e "${BLUE}Available documents in To_Build:${NC}"
    if [ -d "To_Build" ]; then
        count=0
        for file in To_Build/*.md To_Build/*.txt; do
            if [ -f "$file" ]; then
                echo "  - $(basename "$file")"
                ((count++))
            fi
        done
        if [ $count -eq 0 ]; then
            echo -e "${YELLOW}  No markdown or text files found${NC}"
        else
            echo -e "${GREEN}  Total: $count file(s)${NC}"
        fi
    else
        echo -e "${RED}To_Build directory not found${NC}"
    fi
}

# Main logic with error handling
case "$1" in
    --setup|-s)
        setup
        ;;
    --help|-h)
        echo "Usage: $0 [OPTIONS] [FILE]"
        echo ""
        echo "Options:"
        echo "  --setup, -s     Setup/update environment"
        echo "  --all, -a       Build all documents in To_Build directory"
        echo "  --list, -l      List available documents"
        echo "  --clean, -c     Clean PDF output and logs"
        echo "  --clean-logs    Clean only log files"
        echo "  --help, -h      Show this help"
        echo ""
        echo "Examples:"
        echo "  $0              Build all documents"
        echo "  $0 doc.md       Build specific document"
        echo "  $0 --list       List available documents"
        ;;
    --list|-l)
        list_documents
        ;;
    --clean|-c)
        echo -e "${YELLOW}Cleaning output files...${NC}"
        rm -f PDFs/*.pdf
        rm -f Logs/*.log*
        echo -e "${GREEN}✅ PDFs and logs cleaned${NC}"
        ;;
    --clean-logs)
        echo -e "${YELLOW}Cleaning log files...${NC}"
        rm -f Logs/*.log*
        echo -e "${GREEN}✅ Logs cleaned${NC}"
        ;;
    --all|-a|'')
        echo -e "${BLUE}Building all documents...${NC}"
        build --all
        ;;
    *)
        if [ -f "To_Build/$1" ]; then
            echo -e "${BLUE}Building: $1${NC}"
            build "$@"
        else
            echo -e "${RED}❌ Error: File 'To_Build/$1' not found${NC}"
            echo "Use --list to see available documents"
            exit 1
        fi
        ;;
esac