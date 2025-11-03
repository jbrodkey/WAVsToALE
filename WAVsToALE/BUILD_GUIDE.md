# Build Setup for WAVsToALE

## Quick Start

### 1. Push to GitHub
```bash
cd /Users/jasonbrodkey/Documents/SFX/pythonScripts
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/WAVsToALE.git
git push -u origin main
```

### 2. Create a Release
```bash
# Tag a version to trigger build
git tag v1.0.0
git push origin v1.0.0
```

### 3. Download Built Apps
- Go to your GitHub repo → Actions tab
- Wait for build to complete (~5 minutes)
- Download artifacts: `WAVsToALE-macOS` and `WAVsToALE-Windows`

## Local Testing

### Build macOS version locally:
```bash
cd /Users/jasonbrodkey/Documents/SFX/pythonScripts
pip install pyinstaller
./build.sh
```

### Manual build:
```bash
pyinstaller --onefile --windowed --name WAVsToALE wav_to_ale_with_bext_xml_v2_plusUCS-Parsing.py
```

## What the GitHub Action does:

1. **Builds on both platforms**: macOS and Windows runners
2. **Finds UCS CSV automatically**: Includes any CSV file in the build
3. **Creates artifacts**: Downloadable executables for each platform
4. **Auto-releases**: When you push a git tag (v1.0.0, v1.1.0, etc.)

## Next Steps:

1. **Create GitHub repo** for your project
2. **Push this code** to the repo
3. **Tag a release** to trigger the first build
4. **Download your Windows EXE** from the Actions tab!

The Windows executable will work on any Windows 10/11 machine without requiring Python installation.