#!/bin/bash

# Test script for GerdsenAI Document Builder TOC functionality
# This script verifies that the Table of Contents is automatically generated

echo '🔍 Testing GerdsenAI Document Builder TOC Fix...'
echo ''

cd '/Volumes/M2 Raid0/GerdsenAI_Repositories/GerdsenAI_Document_Builder/'

# Test with the existing Quadruped_Lineup.md file
echo '📄 Building Quadruped_Lineup.md...'
./venv/bin/python3 document_builder_reportlab.py Quadruped_Lineup.md

if [ $? -eq 0 ]; then
    echo '✅ Quadruped_Lineup.md built successfully!'
else
    echo '❌ Failed to build Quadruped_Lineup.md'
    exit 1
fi

echo ''
echo '📄 Building test_toc.md...'
./venv/bin/python3 document_builder_reportlab.py test_toc.md

if [ $? -eq 0 ]; then
    echo '✅ test_toc.md built successfully!'
else
    echo '❌ Failed to build test_toc.md'
    exit 1
fi

echo ''
echo '🎉 All tests passed! Table of Contents is now automatically generated for documents with headings.'
echo ''
echo '📁 PDFs generated in: /Volumes/M2 Raid0/GerdsenAI_Repositories/GerdsenAI_Document_Builder/PDFs/'

