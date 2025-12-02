# AAF Master Clip Investigation - Final Report

## 🔍 Investigation Summary

After extensive testing with multiple approaches to create AAF files that import as Master Clips in Avid Media Composer, we've discovered critical stability issues with MasterMob-based approaches.

## 🧪 Tested Approaches

### ❌ Failed Approaches (Crashes/Import Failures)
1. **Pure MasterMob** (following pyaaf2 docs exactly) → **CRASHED AVID MEDIA COMPOSER**
2. **Self-referencing MasterMob** → Segmentation faults  
3. **Hybrid SourceMob** → Imports as subclips only
4. **Master Clip v4** → Doesn't import at all

### ✅ Working Approach (Stable)
**CompositionMob Structure:**
- Creates stable AAF files that import without crashes
- Imports as **subclips** (not master clips)
- Preserves all metadata (BEXT, XML, UCS categories)
- Proven reliable across multiple tests

## 🎯 Final Recommendation

**Use CompositionMob approach + Avid workflow conversion:**

### 1. Technical Implementation
- ✅ Use existing `wav_to_aaf_with_bext_xml_v1_plusUCS-Parsing.py` 
- ✅ Already implements stable CompositionMob approach
- ✅ All metadata preservation working
- ✅ No crashes or import failures

### 2. Workflow Solution  
**In Avid Media Composer:**
1. Import AAF files (they will appear as subclips)
2. Select subclips in bin
3. Right-click → **"Make Master Clip"**
4. OR use batch conversion tools for multiple clips
5. All metadata is preserved during conversion

## 📊 Test Results Summary

| Approach | Avid Import | Stability | Metadata | Result |
|----------|-------------|-----------|----------|---------|
| CompositionMob | ✅ Subclips | ✅ Stable | ✅ Complete | **RECOMMENDED** |
| Pure MasterMob | ❌ Crash | ❌ Crashes Avid | ❌ N/A | Rejected |
| Hybrid SourceMob | ✅ Subclips | ✅ Stable | ✅ Complete | Alternative |
| Self-ref MasterMob | ❌ Segfault | ❌ Crashes Python | ❌ N/A | Rejected |

## 🔧 Production Usage

The current script is **production ready** with the CompositionMob approach:

```bash
# Process single file
python3 wav_to_aaf_with_bext_xml_v1_plusUCS-Parsing.py /path/to/audio.wav

# Process directory
python3 wav_to_aaf_with_bext_xml_v1_plusUCS-Parsing.py /path/to/directory/
```

**Output:** Individual AAF files with embedded audio that import cleanly as subclips, ready for conversion to master clips using Avid's built-in workflow.

## 🎬 Avid Workflow Instructions

### Converting Subclips to Master Clips:

1. **Import AAF files:** File → Import → select AAF files
2. **Locate subclips:** They appear in bin with embedded audio
3. **Convert to master clips:**
   - **Single clip:** Right-click → "Make Master Clip"
   - **Multiple clips:** Select all → Right-click → "Make Master Clip"
   - **Batch processing:** Use Avid's batch tools for large quantities

### Metadata Verification:
- All BEXT metadata preserved in clip properties
- UCS categories maintained in embedded data
- Custom XML metadata accessible through Avid's metadata views

## ✅ Conclusion

**The CompositionMob approach is the optimal solution** because:
- ✅ **Stability:** No crashes or import failures
- ✅ **Reliability:** Consistent behavior across all test files
- ✅ **Metadata:** Complete preservation of all embedded data
- ✅ **Workflow:** Simple one-step conversion in Avid
- ✅ **Production ready:** Can process entire directories safely

**Direct Master Clip creation causes Avid crashes** and should be avoided. The workflow approach provides the same end result (master clips) without stability risks.