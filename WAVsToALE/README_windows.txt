WAVsToALE - Building a Standalone Windows App
============================================

This guide explains how to build a standalone Windows executable for WAVsToALE using PyInstaller.

**Requirements:**
- Windows 10 or later
- Python 3.10+ (from https://www.python.org/downloads/)
- Your script: wav_to_ale_with_bext_xml_v2_plusUCS-Parsing.py
- UCS CSV: UCS_v8.2.1_Full_List.csv (in the same folder as the script)

**Steps:**
1. Open Command Prompt and navigate to your script folder:
   ```cmd
   cd path\to\your\folder
   ```
2. Install PyInstaller:
   ```cmd
   python -m pip install pyinstaller
   ```
3. Build the app (note the semicolon in --add-data for Windows):
   ```cmd
   pyinstaller --noconfirm --clean --windowed --hidden-import tkinter --name "WAVsToALE" --add-data "UCS_v8.2.1_Full_List.csv;." wav_to_ale_with_bext_xml_v2_plusUCS-Parsing.py
   ```
4. After building, your standalone app will be in:
   ```
   dist\WAVsToALE\WAVsToALE.exe
   ```
   You can copy the entire `dist\WAVsToALE` folder to any Windows machine and run `WAVsToALE.exe`.

**Notes:**
- The GUI requires tkinter, which is included with standard Python installers.
- If you see errors about missing DLLs, ensure you used a standard Python from python.org, not the Microsoft Store version.
- The app is self-contained; no Python installation is needed on the target machine.

For questions or updates, contact: jason@editcandy.com
