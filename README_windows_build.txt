WAVsToALE - Windows build and distribution

This app is packaged with PyInstaller. On Windows you can distribute it in two ways:

1) Onedir (folder with .exe + dependencies) - easiest to troubleshoot; ship the whole folder
2) Onefile (single .exe) - easiest to distribute; self-extracts to a temp folder at runtime

Prerequisites
- Windows 10/11
- Python 3.10+ on PATH
- Install PyInstaller: pip install --upgrade pyinstaller

Important: On Windows, --add-data uses a semicolon: "SRC;DEST"

Build commands (run from the project directory)

Onedir build (folder output)
py -m PyInstaller --noconfirm --clean --windowed ^
  --hidden-import tkinter ^
  --name "WAVsToALE" ^
  --add-data "UCS_v8.2.1_Full_List.csv;." ^
  "wav_to_ale_with_bext_xml_v2_plusUCS-Parsing.py"

Output: dist\WAVsToALE\ (contains WAVsToALE.exe and all dependencies)
Ship: zip and share the entire dist\WAVsToALE\ folder

Onefile build (single exe)
py -m PyInstaller --noconfirm --clean --windowed --onefile ^
  --hidden-import tkinter ^
  --name "WAVsToALE" ^
  --add-data "UCS_v8.2.1_Full_List.csv;." ^
  "wav_to_ale_with_bext_xml_v2_plusUCS-Parsing.py"

Output: dist\WAVsToALE.exe
Ship: share just dist\WAVsToALE.exe

Where the UCS CSV goes
- Bundled at build time via --add-data
- At runtime, resource_path(...) uses sys._MEIPASS so it works in both onedir and onefile modes

Troubleshooting
- Missing VCRUNTIME/MSVC DLLs: install Microsoft Visual C++ Redistributable (x64)
- SmartScreen/AV warnings: code-sign the exe or use onedir; reputation improves over time
- Paths with spaces: keep quotes around paths
- Tkinter missing: ensure your Python install includes Tcl/Tk (official python.org installers do)

Using a .spec (optional)
- Generate a .spec by running the onedir command once
- For onefile: edit WAVsToALE.spec to remove the COLLECT(...) block and build with: py -m PyInstaller WAVsToALE.spec
- For onedir: keep the COLLECT(...) block