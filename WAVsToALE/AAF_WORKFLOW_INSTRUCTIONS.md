# AAF Creation and Import Workflow

## Summary
Your script now creates **embedded AAF files** using a **stable CompositionMob approach** that avoids segmentation faults and imports successfully into Avid Media Composer.

## Current Status: ✅ WORKING SOLUTION

### What Works:
- ✅ **AAF Creation**: Script creates embedded AAF files without crashes
- ✅ **Avid Import**: AAF files import successfully into Media Composer  
- ✅ **Embedded Audio**: Audio data is contained within AAF (portable)
- ✅ **Metadata Preservation**: All BEXT, XML, and UCS metadata included
- ✅ **Directory Processing**: Creates individual AAF per WAV file

### Current Limitation:
- ⚠️ **Imports as Subclips**: AAF files import as subclips rather than master clips

## Avid Workflow: Converting Subclips to Master Clips

Since the AAF files import as subclips, use this Avid workflow to convert them to master clips:

### Method 1: Individual Conversion
1. **Import the AAF** files into your Avid project
2. **Right-click** on any subclip in the bin
3. **Select "Make Master Clip"** from context menu
4. **Repeat** for each imported subclip

### Method 2: Batch Conversion
1. **Select all subclips** in the bin (Cmd+A or Ctrl+A)
2. **Right-click** on the selection
3. **Choose "Make Master Clip"** to convert all at once
4. **Confirm** the batch operation

### Method 3: Script/Automation (Advanced)
- Use Avid's scripting tools to automate the conversion process
- Create an Avid macro to batch process multiple subclips

## Technical Details

### AAF Structure Created:
- **CompositionMob**: Timeline/sequence structure (what Avid imports)
- **SourceMob**: Contains embedded audio essence data
- **Metadata**: Preserved as tagged values on CompositionMob

### Why This Approach:
- **Stability**: CompositionMob approach avoids segmentation faults
- **Compatibility**: Structure is recognized and imported by Avid
- **Portability**: Embedded audio means no external file dependencies
- **Completeness**: All metadata from WAV files is preserved

## Running the Script

### Single File:
```bash
python3 wav_to_aaf_with_bext_xml_v1_plusUCS-Parsing.py
```

### Directory Processing:
The script will:
1. **Process all WAV files** in the target directory
2. **Create AAF directory** alongside the WAV directory  
3. **Generate individual AAF** for each WAV file
4. **Preserve metadata** from BEXT, XML, and INFO chunks
5. **Apply UCS categorization** if CSV file is available

### Expected Output:
```
/path/to/wavs/
├── file1.wav
├── file2.wav
└── file3.wav

/path/to/wavs_AAFs/
├── file1.aaf
├── file2.aaf
└── file3.aaf
```

## Next Steps

1. **Test the workflow** with a few AAF files first
2. **Verify subclip to master clip conversion** works as expected
3. **Run full directory processing** when confident
4. **Document any Avid-specific requirements** you discover

## Troubleshooting

### If Import Fails:
- Check Avid version compatibility
- Verify AAF file isn't corrupted
- Try importing smaller/simpler files first

### If Conversion Fails:
- Ensure subclips are properly selected
- Check Avid project settings
- Verify sufficient disk space for master clip creation

### If Metadata Missing:
- Check if metadata was present in original WAV
- Verify UCS CSV file is correct and accessible
- Review script output for metadata parsing warnings

## Alternative Solutions (if needed)

If the subclip workflow proves problematic:
1. **Try mono files** (create single-channel AAFs)
2. **Use different edit rates** (try 25fps, 30fps)  
3. **Export from Pro Tools** (create AAFs from other software)
4. **Use Avid's native import** tools for the WAV files directly

## Success Criteria

✅ **Immediate Goal Achieved**: 
- Embedded AAF files that import into Avid without crashes
- All metadata preserved and accessible
- Portable files with embedded audio

🎯 **Optimal Goal**: 
- Convert subclips to master clips using Avid workflow
- Batch import and processing capability
- Seamless integration into existing Avid projects