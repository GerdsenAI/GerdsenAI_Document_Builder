#!/usr/bin/env python3
"""
GerdsenAI Document Builder - Interactive Setup & Launcher
Run this script to set up the environment and build PDFs.

Usage:
    python3 setup.py
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

# ── Constants ────────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).resolve().parent
VENV_DIR = SCRIPT_DIR / "venv"
VENV_PYTHON = VENV_DIR / "bin" / "python"
REQUIREMENTS = SCRIPT_DIR / "requirements.txt"
CONFIG_FILE = SCRIPT_DIR / "config.yaml"
TO_BUILD_DIR = SCRIPT_DIR / "To_Build"
PDFS_DIR = SCRIPT_DIR / "PDFs"
LOGS_DIR = SCRIPT_DIR / "Logs"
BUILDER_SCRIPT = SCRIPT_DIR / "document_builder_reportlab.py"

# ── Colors (ANSI) ───────────────────────────────────────────────────────────

GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
RED = "\033[0;31m"
BLUE = "\033[0;34m"
CYAN = "\033[0;36m"
BOLD = "\033[1m"
DIM = "\033[2m"
NC = "\033[0m"  # No Color


# ── Helpers ──────────────────────────────────────────────────────────────────

def print_banner():
    print(f"""
{GREEN}╔═══════════════════════════════════════════════════════════╗
║         GerdsenAI Document Builder v2.0.0                 ║
╚═══════════════════════════════════════════════════════════╝{NC}
""")


def print_menu():
    print(f"  {BOLD}[1]{NC}  Build all PDFs")
    print(f"  {BOLD}[2]{NC}  Build a single PDF")
    print(f"  {BOLD}[3]{NC}  Edit settings (config.yaml)")
    print(f"  {BOLD}[4]{NC}  Install / update Playwright & Chromium")
    print(f"  {BOLD}[5]{NC}  Clean PDFs and logs")
    print(f"  {BOLD}[6]{NC}  Clean logs only")
    print(f"  {BOLD}[7]{NC}  Reinstall / update dependencies")
    print(f"  {BOLD}[8]{NC}  Show help")
    print(f"  {BOLD}[0]{NC}  Exit")
    print()


def prompt_choice(prompt_text="Choose an option: "):
    try:
        return input(f"{CYAN}{prompt_text}{NC}").strip()
    except (KeyboardInterrupt, EOFError):
        print()
        return "0"


def run_cmd(cmd, cwd=None, check=True, capture=False):
    """Run a command, streaming output by default."""
    kwargs = dict(cwd=cwd or SCRIPT_DIR, check=check)
    if capture:
        kwargs["capture_output"] = True
        kwargs["text"] = True
    return subprocess.run(cmd, **kwargs)


def ensure_dirs():
    """Create required directories if they don't exist."""
    for d in (TO_BUILD_DIR, PDFS_DIR, LOGS_DIR):
        d.mkdir(exist_ok=True)


# ── Venv Bootstrap ───────────────────────────────────────────────────────────

def is_in_venv():
    """Check if we are running inside the project venv."""
    return (
        hasattr(sys, "prefix")
        and Path(sys.prefix).resolve() == VENV_DIR.resolve()
    )


def create_venv():
    """Create a fresh virtual environment."""
    print(f"\n{YELLOW}Creating virtual environment...{NC}")
    run_cmd([sys.executable, "-m", "venv", str(VENV_DIR)])
    print(f"{GREEN}Virtual environment created at {VENV_DIR}{NC}")


def install_dependencies():
    """Install requirements into the venv."""
    print(f"\n{YELLOW}Upgrading pip...{NC}")
    run_cmd([str(VENV_PYTHON), "-m", "pip", "install", "--upgrade", "pip", "-q"])
    print(f"{YELLOW}Installing dependencies from requirements.txt...{NC}")
    run_cmd([str(VENV_PYTHON), "-m", "pip", "install", "-r", str(REQUIREMENTS)])
    print(f"{GREEN}Dependencies installed successfully.{NC}")


def bootstrap_venv():
    """Ensure the venv exists and has deps installed, then re-exec inside it."""
    first_time = not VENV_DIR.exists()

    if first_time:
        print(f"{YELLOW}First-time setup detected.{NC}")
        create_venv()
        install_dependencies()
        print(f"\n{GREEN}Setup complete!{NC}")
    elif not VENV_PYTHON.exists():
        print(f"{RED}Venv directory exists but Python binary is missing. Recreating...{NC}")
        shutil.rmtree(VENV_DIR)
        create_venv()
        install_dependencies()

    # Re-exec this script inside the venv python
    if not is_in_venv():
        os.execv(str(VENV_PYTHON), [str(VENV_PYTHON), str(Path(__file__).resolve())])


# ── Menu Actions ─────────────────────────────────────────────────────────────

def action_build_all():
    """Build all markdown files in To_Build."""
    md_files = sorted(TO_BUILD_DIR.glob("*.md"))
    if not md_files:
        print(f"\n{YELLOW}No .md files found in {TO_BUILD_DIR.name}/{NC}")
        return

    print(f"\n{BLUE}Building {len(md_files)} document(s)...{NC}\n")
    run_cmd(
        [str(VENV_PYTHON), str(BUILDER_SCRIPT), "--all"],
        check=False,
    )


def action_build_single():
    """Let the user pick a single file to build."""
    md_files = sorted(TO_BUILD_DIR.glob("*.md"))
    if not md_files:
        print(f"\n{YELLOW}No .md files found in {TO_BUILD_DIR.name}/{NC}")
        return

    print(f"\n{BOLD}Available documents:{NC}\n")
    for i, f in enumerate(md_files, 1):
        print(f"  {BOLD}[{i}]{NC}  {f.name}")
    print(f"  {BOLD}[0]{NC}  Cancel")
    print()

    choice = prompt_choice("Select a document: ")
    try:
        idx = int(choice)
    except ValueError:
        print(f"{RED}Invalid selection.{NC}")
        return

    if idx == 0:
        return
    if idx < 1 or idx > len(md_files):
        print(f"{RED}Invalid selection.{NC}")
        return

    selected = md_files[idx - 1]
    print(f"\n{BLUE}Building: {selected.name}{NC}\n")
    run_cmd(
        [str(VENV_PYTHON), str(BUILDER_SCRIPT), selected.name],
        check=False,
    )


def action_edit_settings():
    """Open config.yaml in the user's preferred editor."""
    if not CONFIG_FILE.exists():
        print(f"{RED}config.yaml not found.{NC}")
        return

    editor = os.environ.get("EDITOR")
    if not editor:
        # Try common editors
        for candidate in ("nano", "vi", "vim", "code", "open"):
            if shutil.which(candidate):
                editor = candidate
                break

    if not editor:
        print(f"{RED}No editor found. Set the EDITOR environment variable.{NC}")
        return

    print(f"\n{BLUE}Opening config.yaml with {editor}...{NC}\n")
    run_cmd([editor, str(CONFIG_FILE)], check=False)


def action_install_playwright():
    """Install Playwright and download Chromium."""
    print(f"\n{YELLOW}Installing Playwright browsers (Chromium ~200MB)...{NC}\n")
    run_cmd(
        [str(VENV_PYTHON), "-m", "playwright", "install", "chromium"],
        check=False,
    )
    print(f"\n{GREEN}Playwright setup complete.{NC}")


def action_clean_all():
    """Remove generated PDFs and logs."""
    pdf_count = 0
    log_count = 0

    for f in PDFS_DIR.glob("*.pdf"):
        f.unlink()
        pdf_count += 1

    for f in LOGS_DIR.iterdir():
        if f.is_file():
            f.unlink()
            log_count += 1

    print(f"\n{GREEN}Cleaned {pdf_count} PDF(s) and {log_count} log file(s).{NC}")


def action_clean_logs():
    """Remove log files only."""
    count = 0
    for f in LOGS_DIR.iterdir():
        if f.is_file():
            f.unlink()
            count += 1

    print(f"\n{GREEN}Cleaned {count} log file(s).{NC}")


def action_reinstall_deps():
    """Reinstall/update all dependencies."""
    install_dependencies()


def action_help():
    """Show help and project info."""
    print(f"""
{BOLD}GerdsenAI Document Builder{NC}
{DIM}Convert Markdown files to professional PDFs{NC}

{BOLD}Workflow:{NC}
  1. Place .md files in the {CYAN}To_Build/{NC} directory
  2. Run this script and choose {CYAN}[1] Build all PDFs{NC}
  3. Find generated PDFs in the {CYAN}PDFs/{NC} directory
  4. Check {CYAN}Logs/{NC} for build details

{BOLD}Configuration:{NC}
  Edit {CYAN}config.yaml{NC} to change fonts, colors, margins,
  page size, Mermaid settings, and more.

{BOLD}Mermaid Diagrams:{NC}
  Mermaid diagrams in your Markdown are rendered locally
  via Playwright + Chromium. Run option {CYAN}[4]{NC} to install.

{BOLD}CLI Usage:{NC}
  python3 document_builder_reportlab.py [file.md]    Build one file
  python3 document_builder_reportlab.py --all         Build all files
  ./build_document.sh --help                          Shell script help
""")


# ── Main Loop ────────────────────────────────────────────────────────────────

ACTIONS = {
    "1": action_build_all,
    "2": action_build_single,
    "3": action_edit_settings,
    "4": action_install_playwright,
    "5": action_clean_all,
    "6": action_clean_logs,
    "7": action_reinstall_deps,
    "8": action_help,
}


def main():
    bootstrap_venv()
    ensure_dirs()
    print_banner()

    while True:
        print_menu()
        choice = prompt_choice()

        if choice == "0":
            print(f"\n{GREEN}Goodbye!{NC}\n")
            break

        action = ACTIONS.get(choice)
        if action:
            action()
            print()
        else:
            print(f"{RED}Invalid option. Try again.{NC}\n")


if __name__ == "__main__":
    main()
