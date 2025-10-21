# Virtual Environment Setup Guide

## Quick Start

This project is configured for **automatic venv detection** in VSCode and VSCodium. When you open this folder, the virtual environment will automatically activate.

## Initial Setup (One-Time)

### 1. Create Virtual Environment

```bash
# Navigate to project directory
cd /Volumes/M2\ Raid0/GerdsenAI_Repositories/GerdsenAI_Document_Builder

# Create venv (Python 3.9+ required)
python3 -m venv venv

# Activate venv manually (first time only)
source venv/bin/activate

# Verify activation (should show (venv) prefix)
# (venv) user@machine GerdsenAI_Document_Builder %
```

### 2. Install Dependencies

```bash
# With venv activated, install all packages
pip install --upgrade pip
pip install -r requirements.txt

# Install Chromium for Mermaid rendering (~200MB, one-time)
playwright install chromium

# Verify installations
python -c "from mermaid_cli import render_mermaid_file_sync; print('✓ mermaid-cli ready')"
python -c "import reportlab; print('✓ reportlab ready')"
```

### 3. Reload VSCode/VSCodium

```bash
# Close and reopen VSCode/VSCodium
# OR
# Press Cmd+Shift+P → "Developer: Reload Window"
```

## Automatic Detection

Once configured, the venv will automatically:

✅ **Activate** when you open a new terminal  
✅ **Show** in the status bar (bottom-left): `Python 3.x.x ('venv': venv)`  
✅ **Provide** IntelliSense from venv packages  
✅ **Format** code with Black on save  
✅ **Lint** with Flake8 automatically  

## Verification Checklist

After setup, verify everything works:

- [ ] **Status Bar**: Shows `Python 3.x.x ('venv': venv)` in bottom-left
- [ ] **Terminal**: New terminals show `(venv)` prefix
- [ ] **IntelliSense**: Autocomplete works for `reportlab`, `markdown`, etc.
- [ ] **Build**: Can run `python document_builder_reportlab.py --help`
- [ ] **Mermaid**: Can build docs with Mermaid diagrams

## VSCode/VSCodium Configuration

### Workspace Settings (`.vscode/settings.json`)

The workspace is configured with:

```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
    "python.terminal.activateEnvironment": true,
    "python.terminal.activateEnvInCurrentTerminal": true,
    "editor.formatOnSave": true
}
```

**Key Features:**
- `${workspaceFolder}` = Portable paths (works on any machine)
- `activateEnvironment` = Auto-activates venv in terminals
- `formatOnSave` = Auto-formats Python files with Black

### Recommended Extensions (`.vscode/extensions.json`)

When you open the project, VSCode will suggest installing:

- **Python** - Core Python support
- **Pylance** - Fast IntelliSense and type checking
- **Black Formatter** - Code formatting
- **Flake8** - Linting
- **Markdown All in One** - Markdown editing tools
- **Markdown Lint** - Markdown style checking
- **Markdown Mermaid** - Mermaid diagram preview

## Deactivation

To deactivate the venv (when done working):

```bash
deactivate
```

The next time you open a terminal in VSCode/VSCodium, it will auto-activate again.

## Troubleshooting

### Issue: "Python interpreter not found"

**Solution:**
```bash
# Recreate venv
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium

# Reload VSCode
# Cmd+Shift+P → "Developer: Reload Window"
```

### Issue: Terminal doesn't show (venv) prefix

**Solution:**
1. Check status bar shows correct interpreter
2. Close all terminals
3. Open new terminal (should auto-activate)
4. If still not working, reload window

### Issue: No IntelliSense for packages

**Solution:**
1. Verify venv is activated: `which python` should show `.../venv/bin/python`
2. Check workspace settings: `Cmd+Shift+P` → "Python: Select Interpreter"
3. Choose the one with `('venv': venv)`
4. Reload window

### Issue: "playwright: command not found"

**Solution:**
```bash
# Make sure venv is activated
source venv/bin/activate

# Install Chromium
playwright install chromium

# If that fails, reinstall playwright
pip uninstall playwright
pip install playwright
playwright install chromium
```

### Issue: Settings not auto-loading

**Check:**
1. `.vscode/settings.json` exists in project root
2. VSCode/VSCodium was reloaded after creating venv
3. Python extension is installed

## Manual Activation (If Auto-Activation Fails)

If automatic activation doesn't work:

```bash
# Activate manually each time
source venv/bin/activate

# Then work normally
python document_builder_reportlab.py myfile.md
```

## Environment Details

**Location:** `${workspaceFolder}/venv/`  
**Python:** 3.9+ required  
**Size:** ~500MB (including Chromium)  
**Packages:** See `requirements.txt`  

## Updating Dependencies

To update all packages:

```bash
# Activate venv
source venv/bin/activate

# Update pip
pip install --upgrade pip

# Update all packages
pip install --upgrade -r requirements.txt

# Update Chromium (if needed)
playwright install chromium
```

## Alternative: System-Wide Installation (Not Recommended)

If you absolutely cannot use a venv:

```bash
# Install globally (requires sudo on some systems)
pip3 install -r requirements.txt
playwright install chromium

# Update VSCode settings to use system Python
# In .vscode/settings.json, change:
# "python.defaultInterpreterPath": "/usr/local/bin/python3"
```

**Drawbacks:**
- Packages installed system-wide
- Potential conflicts with other projects
- Harder to manage/troubleshoot
- ~500MB of packages in global Python

## Git Integration

The `.gitignore` is configured to:

✅ **Ignore** the venv directory (`venv/`)  
✅ **Commit** workspace settings (`.vscode/settings.json`)  
✅ **Commit** extension recommendations (`.vscode/extensions.json`)  
✅ **Ignore** user-specific VSCode files  

This means:
- Team members get the same workspace configuration
- Each person creates their own venv locally
- No venv files are committed to the repository

## Working with Multiple Projects

If you work on multiple Python projects:

```bash
# Each project gets its own venv
cd /path/to/project1
source venv/bin/activate  # Activates project1 venv

cd /path/to/project2
source venv/bin/activate  # Activates project2 venv
```

VSCode/VSCodium will automatically switch interpreters when you switch workspace folders.

## Performance Tips

The workspace is configured to exclude venv from file watching:

```json
{
    "files.watcherExclude": {
        "**/venv/**": true
    }
}
```

This prevents VSCode from scanning ~500MB of venv files, improving performance.

## Summary

✅ **One-time setup** - Create venv, install deps, reload VSCode  
✅ **Auto-activation** - Terminals auto-activate venv  
✅ **Portable** - Uses `${workspaceFolder}` for cross-machine compatibility  
✅ **Team-friendly** - Settings committed to Git  
✅ **Performance** - Venv excluded from file watching  

---

**Version**: 1.0.0  
**Last Updated**: October 20, 2025  
**Status**: Production Ready ✅
