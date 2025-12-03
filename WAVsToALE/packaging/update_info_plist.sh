#!/bin/bash
# Update the built app's Info.plist version from Python source
set -euo pipefail

# Resolve script directory and project root
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Paths
PYFILE="$ROOT_DIR/wav_to_ale_with_bext_xml_v2_plusUCS-Parsing.py"
TARGET_PLIST_DEFAULT="$ROOT_DIR/dist/WAVsToALE.app/Contents/Info.plist"
TARGET_PLIST="${1:-$TARGET_PLIST_DEFAULT}"

# Extract version from Python file (__version__ = "x.y.z")
if [[ -f "$PYFILE" ]]; then
  VERSION=$(python3 -c "
import re
with open('$PYFILE', 'r', encoding='utf-8') as f:
    text = f.read()
m = re.search(r'^__version__\s*=\s*[\"\x27]([^\"\x27]+)[\"\x27]', text, re.M)
print(m.group(1) if m else '')
")
else
  VERSION=""
fi

if [[ -z "${VERSION:-}" ]]; then
  VERSION="1.0.0"
fi

# Ensure target plist exists (must be the built app's plist)
if [[ ! -f "$TARGET_PLIST" ]]; then
  echo "Error: Target Info.plist not found at $TARGET_PLIST"
  echo "Build the app first, then run this script."
  exit 1
fi

PLISTBUDDY="/usr/libexec/PlistBuddy"

# Helper to set or add a key
set_or_add() {
  local key="$1"; local value="$2"; local type="${3:-string}"
  if "$PLISTBUDDY" -c "Print :$key" "$TARGET_PLIST" >/dev/null 2>&1; then
    "$PLISTBUDDY" -c "Set :$key $value" "$TARGET_PLIST"
  else
    "$PLISTBUDDY" -c "Add :$key $type $value" "$TARGET_PLIST"
  fi
}

# Update keys
set_or_add CFBundleName WAVsToALE
set_or_add CFBundleDisplayName WAVsToALE
set_or_add CFBundleIdentifier com.editcandy.wavstoale
set_or_add CFBundleShortVersionString "$VERSION"
set_or_add CFBundleVersion "$VERSION"

echo "Updated $TARGET_PLIST to version $VERSION"
