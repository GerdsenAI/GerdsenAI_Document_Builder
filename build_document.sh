#!/bin/bash

# GerdsenAI Document Builder
# Consolidated build script

# Get the directory of this script
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

# Colors
GREEN='[0;32m'
YELLOW='[1;33m'
NC='[0m'

echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║      🚀 GerdsenAI Document Builder v2.0.0 🚀            ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"

# Function to setup environment
setup() {
    echo -e "${YELLOW}Setting up environment...${NC}"
    
    # Create venv if it doesn't exist
    if [ ! -d "venv" ]; then
        echo "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate and install packages
    source venv/bin/activate
    pip install --upgrade pip > /dev/null 2>&1
    pip install --upgrade markdown reportlab pillow beautifulsoup4 pyyaml watchdog pygments > /dev/null 2>&1
    
    echo -e "${GREEN}✅ Setup complete!${NC}"
}

# Function to build documents
build() {
    if [ ! -d "venv" ]; then
        setup
    fi
    source venv/bin/activate
    python document_builder.py "$@"
}

# Main logic
case "$1" in
    --setup|-s)
        setup
        ;;
    --help|-h)
        echo "Usage: $0 [OPTIONS] [FILE]"
        echo "Options:"
        echo "  --setup, -s    Setup/update environment"
        echo "  --all, -a      Build all documents"
        echo "  --clean, -c    Clean PDF output"
        echo "  --help, -h     Show this help"
        ;;
    --clean|-c)
        rm -f PDFs/*.pdf
        echo -e "${GREEN}PDFs cleaned${NC}"
        ;;
    --all|-a|'')
        build --all
        ;;
    *)
        build "$@"
        ;;
esac

