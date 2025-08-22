#!/usr/bin/env python3
"""
Setup script for GerdsenAI Document Builder
Installs all required dependencies
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(command, silent=False):
    """Run a shell command and return success status."""
    try:
        if silent:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
        else:
            result = subprocess.run(command, shell=True)
        return result.returncode == 0
    except Exception as e:
        print(f"Error running command: {e}")
        return False

def main():
    print("=" * 60)
    print("GerdsenAI Document Builder Setup")
    print("=" * 60)
    
    # Get repository path
    repo_path = Path(__file__).parent
    venv_path = repo_path / "venv"
    
    # Step 1: Create virtual environment
    if not venv_path.exists():
        print("\nCreating virtual environment...")
        if not run_command(f"python3 -m venv '{venv_path}'"):
            print("Failed to create virtual environment")
            sys.exit(1)
        print("Virtual environment created")
    else:
        print("Virtual environment already exists")
    
    # Step 2: Upgrade pip
    print("\nUpgrading pip...")
    pip_path = venv_path / "bin" / "pip"
    if not run_command(f"'{pip_path}' install --upgrade pip", silent=True):
        print("Warning: Could not upgrade pip")
    else:
        print("Pip upgraded")
    
    # Step 3: Install requirements
    print("\nInstalling required packages...")
    requirements_file = repo_path / "requirements.txt"
    
    # If requirements.txt doesn't exist, use inline list
    if requirements_file.exists():
        if not run_command(f"'{pip_path}' install -r '{requirements_file}'"):
            print("Failed to install from requirements.txt")
            sys.exit(1)
    else:
        packages = [
            "markdown>=3.5.0",
            "reportlab>=4.0.0",
            "Pillow>=10.0.0",
            "beautifulsoup4>=4.12.0",
            "pygments>=2.16.0",
            "pyyaml>=6.0",
            "watchdog>=3.0.0"
        ]
        
        for package in packages:
            pkg_name = package.split('>=')[0]
            print(f"  Installing {pkg_name}...")
            if not run_command(f"'{pip_path}' install '{package}'", silent=True):
                print(f"  Warning: Issue installing {package}")
    
    print("All packages installed")
    
    # Step 4: Check for optional dependencies
    print("\nChecking optional dependencies...")
    
    # Check for mermaid-cli
    if run_command("which mmdc", silent=True):
        print("Mermaid CLI found")
    else:
        print("Mermaid CLI not found")
        print("   To enable Mermaid diagram support, run:")
        print("   npm install -g @mermaid-js/mermaid-cli")
    
    # Step 5: Create test file for verification
    test_file = repo_path / "test_imports.py"
    with open(test_file, 'w') as f:
        f.write("""
import sys
try:
    import markdown
    import reportlab
    from PIL import Image
    from bs4 import BeautifulSoup
    # import pymupdf - removed, not needed with reportlab
    import yaml
    print("All core modules imported successfully")
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)
""")
    
    print("\nVerifying installation...")
    python_path = venv_path / "bin" / "python3"
    if not run_command(f"'{python_path}' '{test_file}'"):
        print("Verification failed")
        sys.exit(1)
    
    # Clean up test file
    test_file.unlink()
    
    print("\n" + "=" * 60)
    print("Setup complete!")
    print("=" * 60)
    print("\nYou can now build documents with:")
    print("   ./build_document.sh")
    print("   ./build_document.sh document.md")
    print("   ./build_document.sh --all")
    print("\nFor help, run:")
    print("   ./build_document.sh --help")

if __name__ == "__main__":
    main()
