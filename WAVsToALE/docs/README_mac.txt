WAVsToALE - Building a Standalone Mac App
========================================

This guide explains how to build a standalone Mac app for WAVsToALE using PyInstaller.

**Requirements:**
- macOS 12 or later (Apple Silicon or Intel)
- Python 3.10+ (from https://www.python.org/downloads/)
- Your script: wav_to_ale_with_bext_xml_v2_plusUCS-Parsing.py (UCS data is embedded; no external CSV needed)

**Steps:**
1. Open Terminal and navigate to your script folder:
   ```sh
   cd /path/to/your/folder
   ```
2. Install PyInstaller:
   ```sh
   python3 -m pip install --user pyinstaller
   ```
3. Build the app (UCS data is embedded; no CSV flag needed):
   ```sh
   python3 -m PyInstaller --noconfirm --clean --windowed --hidden-import tkinter --name "WAVsToALE" wav_to_ale_with_bext_xml_v2_plusUCS-Parsing.py
   ```
4. After building, your standalone app will be in:
   ```
   dist/WAVsToALE.app
   ```
   You can copy the `WAVsToALE.app` bundle anywhere and run it by double-clicking.

**Notes:**
- The GUI requires tkinter, which is included with standard Python installers.
- If you see errors about missing Tcl/Tk, ensure you used a standard Python from python.org, not Homebrew or the Mac App Store.
- The app is self-contained; no Python installation is needed on the target machine.
- If Gatekeeper blocks the app, right-click and choose "Open" the first time.

For questions or updates, contact: jason@editcandy.com
