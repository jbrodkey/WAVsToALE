#!/bin/bash
# Build script for WAVsToALE

echo "Building WAVsToALE..."

# Check if UCS CSV exists
if [ -f "UCS_v8.2.1_Full_List.csv" ]; then
    echo "Found UCS CSV file, including in build..."
    DATA_FLAG="--add-data UCS_v8.2.1_Full_List.csv:."
elif ls *.csv 1> /dev/null 2>&1; then
    CSV_FILE=$(ls *.csv | head -1)
    echo "Found CSV file: $CSV_FILE, including in build..."
    DATA_FLAG="--add-data $CSV_FILE:."
else
    echo "No UCS CSV found, building without..."
    DATA_FLAG=""
fi

# Check for icon file
if [ -f "icons/mac/WAVsToALE.icns" ]; then
    echo "Found macOS icon, including in build..."
    ICON_FLAG="--icon icons/mac/WAVsToALE.icns"
else
    echo "No icon found, building without custom icon..."
    ICON_FLAG=""
fi

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build/ dist/ *.spec

# Build with PyInstaller (onedir mode for macOS)
echo "Building application..."
pyinstaller \
    --onedir \
    --windowed \
    --name WAVsToALE \
    $ICON_FLAG \
    --hidden-import=tkinter \
    --hidden-import=tkinter.ttk \
    --hidden-import=tkinter.filedialog \
    --hidden-import=tkinter.messagebox \
    --hidden-import=tkinter.font \
    --hidden-import=tkinter.scrolledtext \
    $DATA_FLAG \
    wav_to_ale_with_bext_xml_v2_plusUCS-Parsing.py

echo "Build complete! Check dist/ folder for WAVsToALE.app"