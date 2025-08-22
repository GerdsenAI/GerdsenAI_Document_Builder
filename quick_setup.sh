#!/bin/bash

echo "======================================"
echo "GerdsenAI Document Builder Setup"
echo "======================================"

# Navigate to repo
cd "/Volumes/M2 Raid0/GerdsenAI_Repositories/GerdsenAI_Document_Builder"

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate it
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install packages
echo "Installing packages..."
pip install markdown reportlab Pillow beautifulsoup4 pygments pyyaml watchdog

echo ""
echo "======================================"
echo "Setup Complete!"
echo "======================================"
echo ""
echo "Test with: ./build_document.sh --list"
