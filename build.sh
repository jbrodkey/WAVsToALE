#!/bin/bash
# Build script for WAVsToALE

echo "Building WAVsToALE..."

# Check if UCS CSV exists
if [ -f "UCS_v8.2.1_Full_List.csv" ]; then
    echo "Found UCS CSV file, including in build..."
    DATA_FLAG="--add-data UCS_v8.2.1_Full_List.csv:."
elif [ -f "*.csv" ]; then
    CSV_FILE=$(ls *.csv | head -1)
    echo "Found CSV file: $CSV_FILE, including in build..."
    DATA_FLAG="--add-data $CSV_FILE:."
else
    echo "No UCS CSV found, building without..."
    DATA_FLAG=""
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
    $DATA_FLAG \
    wav_to_ale_with_bext_xml_v2_plusUCS-Parsing.py

echo "Build complete! Check dist/ folder for WAVsToALE.app"