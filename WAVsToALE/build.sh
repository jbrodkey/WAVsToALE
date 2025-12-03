#!/bin/bash
# Build script for WAVsToALE

echo "Building WAVsToALE..."

# Check if UCS CSV exists (prefer data/)
if [ -f "data/UCS_v8.2.1_Full_List.csv" ]; then
    echo "Found UCS CSV in data/, including in build..."
    DATA_FLAG="--add-data data/UCS_v8.2.1_Full_List.csv:data"
elif ls data/*.csv 1> /dev/null 2>&1; then
    CSV_FILE=$(ls data/*.csv | head -1)
    echo "Found CSV file in data/: $CSV_FILE, including in build..."
    DATA_FLAG="--add-data $CSV_FILE:data"
elif ls *.csv 1> /dev/null 2>&1; then
    CSV_FILE=$(ls *.csv | head -1)
    echo "Found CSV file in project root: $CSV_FILE, including in build..."
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


# No pre-build Info.plist update; we'll update the built app's plist post-build.

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build/ dist/

# Build with PyInstaller using spec file (includes version info)
echo "Building application..."
pyinstaller WAVsToALE.spec


echo "Build complete! Check dist/ folder for WAVsToALE.app"

# Update built app Info.plist with version from Python source
echo "Updating app Info.plist with version..."
./packaging/update_info_plist.sh || {
    echo "Info.plist update failed; ensure app exists at dist/WAVsToALE.app";
    exit 1;
}

# Run automated validation
echo "Running automated validation..."
./validate_bundle.sh