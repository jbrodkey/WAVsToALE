"""
This script creates Embedded Advanced Authoring Format (AAF) files by parsing metadata from SFX WAV files.
It extracts metadata from:
- Standard WAV properties
- Broadcast audio metadata (BEXT)
- Embedded XML
- File naming conventions (UCS categories)
 
It will generate individual embedded AAF files for each WAV file found:
- If input is a single WAV file: creates one AAF file
- If input is a directory: creates individual AAF files for each WAV, maintaining directory structure

The resulting embedded AAF files contain the actual audio data (not just references) along with 
all extracted metadata, making them completely portable and suitable for import into 
Avid Media Composer and other AAF-compatible applications without requiring the original WAV files.

This has been tested on macOS. Your mileage may vary on other operating systems.

Author: Jason Brodkey
Contact: jason@editcandy.com
Copyright (c) 2025 Jason Brodkey. All rights reserved.

"""

__version__ = "1.0.0"

import os
import csv
import wave
import io
import struct
from xml.etree.ElementTree import iterparse
from concurrent.futures import ThreadPoolExecutor
import sys
import threading
import subprocess
import tempfile
import shutil
try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox, font
    from tkinter.scrolledtext import ScrolledText
    # Test basic tkinter functionality to ensure it's fully working
    try:
        test_root = tk.Tk()
        test_root.withdraw()  # Hide the test window
        test_root.destroy()   # Clean up
    except Exception:
        # tkinter imported but can't create windows
        tk = None
        ttk = None
        filedialog = None
        messagebox = None
        ScrolledText = None
except Exception as _tk_err:
    # GUI is optional; script still works in CLI mode without tkinter
    tk = None
    ttk = None
    filedialog = None
    messagebox = None
    ScrolledText = None
    # Log the tkinter import error for troubleshooting packaged app launch issues
    try:
        import traceback, datetime, tempfile
        ts = datetime.datetime.now().isoformat()
        log_path = os.path.join(tempfile.gettempdir(), 'WavToAAF_gui_error.log')
        with open(log_path, 'a', encoding='utf-8') as _f:
            _f.write(f"[{ts}] tkinter import failed:\n")
            _f.write(''.join(traceback.format_exception(_tk_err)))
            _f.write("\n")
    except Exception:
        pass

# Try to import AAF library
try:
    import aaf2
    AAF_AVAILABLE = True
except ImportError:
    AAF_AVAILABLE = False
    print("Warning: pyaaf2 library not found. Please install it using: pip install pyaaf2")

# Global UCS mapping dictionary
UCS_MAPPING = {}
# Collect skipped files/errors for later logging (silently skip during run)
SKIP_LOG = []

def resource_path(relative_path):
    """Get absolute path to resource, works for PyInstaller and normal execution.

    When bundled with PyInstaller, data files are unpacked to a temporary folder
    accessible via sys._MEIPASS. Fallback to the script directory when not bundled.
    """
    try:
        base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.realpath(__file__)))
    except Exception:
        base = os.getcwd()
    return os.path.join(base, relative_path)

def load_ucs_mapping(csv_file_path):
    """Load UCS mapping from a CSV file."""
    ucs_mapping = {}
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as csv_file:
            reader = csv.DictReader(csv_file)
            if not reader.fieldnames:
                print("Error: CSV file has no header row.")
                return {}

            # Build a case-insensitive map of header -> original header
            headers = [h.strip() for h in reader.fieldnames]
            lower_map = {h.lower(): h for h in headers}

            # Required keys (case-insensitive)
            required = ['catid', 'category', 'subcategory']
            if not all(k in lower_map for k in required):
                print(f"Error: CSV file is missing required columns (CatID, Category, Subcategory). Found headers: {headers}")
                return {}

            # Use the actual header names when reading rows to preserve original casing
            catid_h = lower_map['catid']
            category_h = lower_map['category']
            subcategory_h = lower_map['subcategory']

            for row in reader:
                cat_id = (row.get(catid_h) or '').strip().upper()
                category = (row.get(category_h) or 'Unknown').strip()
                subcategory = (row.get(subcategory_h) or 'Unknown').strip()
                if cat_id:
                    ucs_mapping[cat_id] = (category, subcategory)
    except Exception as e:
        print(f"Error loading UCS mapping from CSV: {e}")
    return ucs_mapping

def extract_ucs_category(filename):
    """Extract CatID from filename and map to Category and Subcategory."""
    # Assume CatID is the first part of the filename before an underscore
    cat_id = filename.split('_')[0].upper()
    category, subcategory = UCS_MAPPING.get(cat_id, ("", ""))  # Return empty strings if CatID is not found
    return category, subcategory

def parse_wav_metadata(wav_file_path, fps: float = 24.0):
    """Extract metadata from a WAV file, including BEXT, XML, and INFO chunks.

    fps may be a non-integer (e.g. 23.976, 29.97) and is used to compute the
    SMPTE "End" timecode's frame value. The function will round frames and
    carry any overflow into seconds/minutes/hours as needed.
    """
    metadata = {}
    try:
        # Use wave to get audio properties
        with wave.open(wav_file_path, 'rb') as wf:
            # Keep full precision for duration (seconds as float)
            duration = wf.getnframes() / wf.getframerate()
            # Whole seconds and fractional part
            whole_seconds = int(duration)
            frac = duration - whole_seconds
            # Compute frames with rounding. If frames == fps after rounding,
            # carry into the whole seconds.
            frames = int(round(frac * float(fps)))
            if frames >= int(round(float(fps))):
                frames = 0
                whole_seconds += 1

            seconds = whole_seconds % 60
            minutes = (whole_seconds // 60) % 60
            hours = whole_seconds // 3600
            smpte_duration = f"{hours:02}:{minutes:02}:{seconds:02}:{frames:02}"

            channels = wf.getnchannels()
            tracks = "A1" if channels == 1 else "A1A2" if channels == 2 else f"A1A{channels}"

            metadata.update({
                "Name": sanitize_string(os.path.basename(wav_file_path)),
                "Tape": "",
                "Start": "00:00:00:00",
                "End": smpte_duration,
                "Tracks": tracks,
                "AudioFormat": "WAV",
                "Filename": sanitize_string(os.path.basename(wav_file_path)),
                "Channels": channels,
                "Sample Width": wf.getsampwidth(),
                "Sample Rate": wf.getframerate(),
                "Number of Frames": wf.getnframes(),
                "Duration": duration,
                "File Path": wav_file_path,  # Add full path for AAF embedding
            })

        # Read raw file bytes so we can locate metadata chunks (bext, XML, INFO)
        with open(wav_file_path, 'rb') as f:
            data = f.read()
            metadata.update(parse_bext_chunk(data))
            metadata.update(parse_xml_chunk(data))
            metadata.update(parse_info_chunk(data))

        # Extract UCS category from filename
        filename = os.path.basename(wav_file_path)
        category, subcategory = extract_ucs_category(filename)
        metadata['Category'] = category
        metadata['Subcategory'] = subcategory

    except EOFError as e:
        # Record and skip files with EOF or other read errors
        try:
            SKIP_LOG.append(f"{wav_file_path}\tEOFError: {e}")
        except Exception:
            pass
        return None
    except wave.Error as e:
        # Record unsupported/unknown WAV formats and skip them silently
        try:
            SKIP_LOG.append(f"{wav_file_path}\tWaveError: {e}")
        except Exception:
            pass
        return None
    except Exception as e:
        try:
            SKIP_LOG.append(f"{wav_file_path}\tError: {e}")
        except Exception:
            pass
        return None

    return metadata

def parse_bext_chunk(data):
    """Parse the BEXT chunk from the WAV file."""
    bext_metadata = {}
    try:
        bext_start = data.find(b'bext')
        if bext_start != -1:
            # Skip the 'bext' identifier and chunk size (8 bytes total)
            bext_start += 8
            # Extract fields from the BEXT chunk (fixed sizes)
            description = sanitize_string(data[bext_start:bext_start + 256].decode('ascii', errors='ignore'))
            originator = sanitize_string(data[bext_start + 256:bext_start + 256 + 32].decode('ascii', errors='ignore'))
            originator_ref = sanitize_string(data[bext_start + 288:bext_start + 288 + 32].decode('ascii', errors='ignore'))
            origination_date = sanitize_string(data[bext_start + 320:bext_start + 320 + 10].decode('ascii', errors='ignore'))
            origination_time = sanitize_string(data[bext_start + 330:bext_start + 330 + 8].decode('ascii', errors='ignore'))

            bext_metadata.update({
                'Description': description,
                'Originator': originator,
                'Originator Reference': originator_ref,
                'Origination Date': origination_date,
                'Origination Time': origination_time,
            })
    except Exception as e:
        print(f"Error parsing BEXT chunk: {e}")
    return bext_metadata

def parse_xml_chunk(data):
    """Parse the XML chunk from the WAV file."""
    xml_metadata = {}
    try:
        xml_start = data.find(b'<ebucore:ebuCoreMain')
        if xml_start != -1:
            xml_end = data.find(b'</ebucore:ebuCoreMain>') + len(b'</ebucore:ebuCoreMain>')
            xml_data = data[xml_start:xml_end].decode('utf-8', errors='ignore')

            # Parse XML data
            for event, elem in iterparse(io.StringIO(xml_data), events=("start", "end")):
                if event == "end" and elem.text:
                    tag = elem.tag.split('}')[-1]  # Remove namespace
                    xml_metadata[tag] = sanitize_string(elem.text.strip())
    except Exception as e:
        print(f"Error parsing XML chunk: {e}")
    return xml_metadata

def parse_info_chunk(data):
    """Parse the INFO chunk from the WAV file."""
    info_metadata = {}
    try:
        offset = 0
        while True:
            info_start = data.find(b'LIST', offset)
            if info_start == -1:
                break
            # Read LIST chunk size (4 bytes little-endian)
            if info_start + 8 > len(data):
                break
            list_size = struct.unpack('<I', data[info_start + 4:info_start + 8])[0]
            list_type = data[info_start + 8:info_start + 12]
            # We only care about INFO lists
            if list_type == b'INFO':
                # Start of INFO subchunks
                sub_offset = info_start + 12
                end_of_list = info_start + 8 + list_size
                while sub_offset + 8 <= end_of_list and sub_offset + 8 <= len(data):
                    chunk_id = data[sub_offset:sub_offset + 4]
                    chunk_size = struct.unpack('<I', data[sub_offset + 4:sub_offset + 8])[0]
                    data_start = sub_offset + 8
                    data_end = data_start + chunk_size
                    if data_end > len(data):
                        break
                    chunk_data = data[data_start:data_end].split(b'\x00')[0].decode('utf-8', errors='ignore').strip()
                    try:
                        info_metadata[chunk_id.decode('ascii')] = sanitize_string(chunk_data)
                    except Exception:
                        info_metadata[str(chunk_id)] = sanitize_string(chunk_data)
                    # Chunks are word aligned: if chunk_size is odd, there's a pad byte
                    pad = 1 if (chunk_size % 2) == 1 else 0
                    sub_offset = data_end + pad
            # Move forward to look for another LIST
            offset = info_start + 4
    except Exception as e:
        print(f"Error parsing INFO chunk: {e}")
    return info_metadata

def sanitize_string(value):
    """Remove null bytes, non-printable characters, tabs, newlines, and non-ASCII characters for compatibility."""
    if value:
        # Replace tabs, newlines, and carriage returns with spaces first
        cleaned = value.replace('\t', ' ').replace('\n', ' ').replace('\r', ' ')
        # Remove non-printable characters
        cleaned = ''.join(char for char in cleaned if char.isprintable())
        # Remove non-ASCII characters for strict compatibility (only allow ASCII 0-127)
        cleaned = ''.join(char for char in cleaned if ord(char) < 128)
        # Collapse multiple spaces into single space and strip
        cleaned = ' '.join(cleaned.split())
        return cleaned
    return ""

def sanitize_path(path_str):
    """Normalize a path string coming from user input.

    - Strips surrounding single or double quotes if present
    - Expands ~ and environment variables
    - Returns absolute path
    """
    if path_str is None:
        return path_str
    s = path_str.strip()
    # Try to interpret shell-style escaping/quoting (so users can paste paths like: /path/with\ spaces)
    try:
        import shlex
        parts = shlex.split(s)
        if parts:
            s = parts[0]
    except Exception:
        # Fallback: unescape common escaped characters (spaces, commas, parentheses, ampersand, etc.)
        # e.g. user pastes: /path/with\ spaces or /Folder/Carpet\ Footsteps\,\ Trainers
        unescapes = {'\\ ': ' ', '\\,': ',', '\\(': '(', '\\)': ')', '\\&': '&', "\\'": "'", '\\"': '"', '\\#': '#'}
        for esc, char in unescapes.items():
            s = s.replace(esc, char)

    # Remove surrounding matching quotes as a last resort
    if (s.startswith("'") and s.endswith("'")) or (s.startswith('"') and s.endswith('"')):
        s = s[1:-1]

    s = os.path.expanduser(os.path.expandvars(s))
    try:
        s = os.path.abspath(s)
    except Exception:
        pass
    return s

def get_unique_filepath(filepath):
    """
    Generate a unique file path by appending a number if the file already exists.
    e.g., file.aaf -> file_1.aaf -> file_2.aaf, etc.
    """
    if not os.path.exists(filepath):
        return filepath
    
    base, ext = os.path.splitext(filepath)
    counter = 1
    while True:
        new_path = f"{base}_{counter}{ext}"
        if not os.path.exists(new_path):
            return new_path
        counter += 1

def create_embedded_aaf_file(wav_file_path, metadata, output_file_path, fps=24):
    """Create a single embedded AAF file with the audio data included, using CompositionMob approach for stability. Returns the actual path used."""
    if not metadata:
        print("Error: No metadata to write to AAF file.")
        return None

    if not AAF_AVAILABLE:
        print("Error: pyaaf2 library not available. Cannot create AAF files.")
        return None

    if not os.path.exists(wav_file_path):
        print(f"Error: Audio file not found: {wav_file_path}")
        return None

    # Check if file exists and get unique path if needed
    output_file_path = get_unique_filepath(output_file_path)

    try:
        # Create AAF file using stable CompositionMob approach
        with aaf2.open(output_file_path, 'w') as f:
            # Get clip name for naming conventions
            clip_name = metadata.get('Name', os.path.splitext(os.path.basename(wav_file_path))[0])
            
            # Get audio properties
            channels = metadata.get('Channels', 1)
            duration_seconds = metadata.get('Duration', 0)
            duration_frames = int(duration_seconds * fps)
            
            # Step 1: Create SourceMob with embedded audio
            temp_master = f.create.MasterMob(f"{clip_name}_temp")
            temp_master.import_audio_essence(wav_file_path, edit_rate=fps)
            
            # Find the created SourceMob
            source_mobs = [mob for mob in f.content.mobs if type(mob).__name__ == 'SourceMob']
            if not source_mobs:
                print("Error: No SourceMob created during audio import")
                return None
            
            source_mob = source_mobs[0]
            
            # Step 2: Create CompositionMob (stable approach that imports successfully)
            comp_mob = f.create.CompositionMob(f"{clip_name}_composition")
            
            # Step 3: Create timeline tracks in CompositionMob that reference SourceMob
            for channel in range(channels):
                # Create timeline slot
                slot = f.create.TimelineMobSlot()
                slot.name = f"{clip_name}_ch{channel+1}"
                slot.slot_id = channel + 1
                slot.edit_rate = fps
                slot.origin = 0
                
                # Create source clip that references the embedded audio
                source_clip = f.create.SourceClip()
                source_clip.length = duration_frames
                source_clip.start = 0
                source_clip.datadef = f.dictionary.lookup_datadef('Sound')
                
                # Reference the SourceMob
                source_clip.mob = source_mob
                source_clip.slot_id = 1  # Reference the audio slot in SourceMob
                
                slot.segment = source_clip
                comp_mob.slots.append(slot)
            
            # Rename temp_master to avoid confusion
            temp_master.name = f"{clip_name}_temp_master"
            
            # Add CompositionMob to the AAF
            f.content.mobs.append(comp_mob)
            
            # Add metadata as tagged values to the composition mob
            metadata_fields = [
                ('Description', metadata.get('Description', '')),
                ('Category', metadata.get('Category', '')),
                ('Subcategory', metadata.get('Subcategory', '')),
                ('Originator', metadata.get('Originator', '')),
                ('Originator_Reference', metadata.get('Originator Reference', '')),
                ('Origination_Date', metadata.get('Origination Date', '')),
                ('Origination_Time', metadata.get('Origination Time', '')),
                ('Filename', metadata.get('Filename', '')),
                ('Sample_Rate', str(metadata.get('Sample Rate', ''))),
                ('Channels', str(metadata.get('Channels', ''))),
                ('Duration', str(metadata.get('Duration', ''))),
                ('Start', metadata.get('Start', '')),
                ('End', metadata.get('End', '')),
                ('Tracks', metadata.get('Tracks', '')),
                ('AudioFormat', metadata.get('AudioFormat', '')),
            ]
            
            # Add metadata to the composition mob comments
            for tag_name, tag_value in metadata_fields:
                if tag_value and str(tag_value).strip():
                    try:
                        tagged_value = f.create.TaggedValue()
                        tagged_value.name = tag_name
                        tagged_value.value = str(tag_value).strip()
                        comp_mob.comments.append(tagged_value)
                    except Exception as e:
                        print(f"Warning: Could not add {tag_name} metadata: {e}")

        print(f"Successfully created embedded AAF file: {output_file_path}")
        print(f"Note: AAF will import as subclips. See workflow notes for master clip conversion.")
        return output_file_path

    except Exception as e:
        print(f"Error creating embedded AAF file: {e}")
        import traceback
        traceback.print_exc()
        return None

    except Exception as e:
        print(f"Error creating embedded AAF file: {e}")
        import traceback
        traceback.print_exc()
        return None

def run_conversion(ucs_csv_file, wav_path, output_aaf_file, fps=24, logger=print, cancel_event: threading.Event | None = None, output_paths: list | None = None):
    """Run the conversion using existing logic without interactive prompts.

    Parameters:
    - ucs_csv_file: Optional path to UCS CSV. If None or invalid, attempt default lookup in script directory.
    - wav_path: Path to a single WAV file or a directory containing WAVs.
    - output_aaf_file: Optional desired AAF output path; default location will be used if not provided.
    - fps: Integer FPS for AAF timeline.
    - logger: Function to consume log strings (defaults to print). GUI can pass a custom logger.
    - output_paths: Optional list to collect actual AAF file paths created (for GUI tracking).
    """
    global UCS_MAPPING
    
    if not AAF_AVAILABLE:
        logger("Error: pyaaf2 library not available. Please install it using: pip install pyaaf2")
        return False
    
    # Initialize output_paths list for tracking if provided
    if output_paths is not None and not isinstance(output_paths, list):
        output_paths = None

    # Resolve base directory for resources (PyInstaller or script dir)
    try:
        script_dir = os.path.dirname(os.path.realpath(__file__))
    except Exception:
        script_dir = os.getcwd()
    base_dir = getattr(sys, "_MEIPASS", script_dir)

    # UCS CSV resolution: use provided, else try defaults in bundled base
    if not ucs_csv_file or not os.path.isfile(ucs_csv_file):
        default_name = 'data/UCS_v8.2.1_Full_List.csv'
        default_ucs = resource_path(default_name)
        if os.path.isfile(default_ucs):
            ucs_csv_file = default_ucs
            # Show friendly message instead of /var/... path in GUI
            if getattr(sys, 'frozen', False):
                logger("Using built-in UCS source")
            else:
                logger(f"Using UCS CSV: {ucs_csv_file}")
        else:
            # Fallback: any CSV with 'ucs' in the name in the base dir
            try:
                for fname in os.listdir(base_dir):
                    if fname.lower().endswith('.csv') and 'ucs' in fname.lower():
                        ucs_csv_file = os.path.join(base_dir, fname)
                        if getattr(sys, 'frozen', False):
                            logger("Using built-in UCS source")
                        else:
                            logger(f"Using UCS CSV found in resources: {ucs_csv_file}")
                        break
            except Exception:
                pass

    if not ucs_csv_file or not os.path.isfile(ucs_csv_file):
        logger("Error: No valid UCS CSV file provided.")
        return False

    # Validate wav_path
    if not wav_path:
        logger("Error: No WAV file or directory provided.")
        return False
    is_single_file = os.path.isfile(wav_path)
    is_directory = os.path.isdir(wav_path)
    if not is_single_file and not is_directory:
        logger(f"Error: Path does not exist or is not a file/directory: {wav_path}")
        return False

    # Load UCS mapping
    UCS_MAPPING = load_ucs_mapping(ucs_csv_file)
    if not UCS_MAPPING:
        logger("Error: Failed to load UCS mapping. Ensure the CSV file is valid.")
        return False

    # Single WAV file case
    if is_single_file:
        if not wav_path.lower().endswith('.wav'):
            logger(f"Error: File is not a WAV file: {wav_path}")
            return False

        wav_basename = os.path.splitext(os.path.basename(wav_path))[0]
        if not output_aaf_file:
            # Place default output inside a folder named after the WAV
            wav_parent = os.path.dirname(wav_path)
            aafs_dir = os.path.join(wav_parent, 'AAFs')
            try:
                os.makedirs(aafs_dir, exist_ok=True)
            except Exception:
                pass
            output_aaf_file = os.path.join(aafs_dir, wav_basename, f"{wav_basename}.aaf")
            logger(f"Using default AAF filepath: {output_aaf_file}")
        elif os.path.isdir(output_aaf_file):
            output_aaf_file = os.path.join(output_aaf_file, f"{wav_basename}.aaf")
            logger(f"Output path is a directory. Using default file: {output_aaf_file}")
        try:
            os.makedirs(os.path.dirname(output_aaf_file), exist_ok=True)
        except Exception:
            pass

        logger(f"Processing single WAV file: {wav_path}")
        metadata = parse_wav_metadata(wav_path, fps)
        if metadata:
            actual_path = create_embedded_aaf_file(wav_path, metadata, output_aaf_file, fps)
            if actual_path:
                if output_paths is not None:
                    output_paths.append(actual_path)
                logger(f"Successfully created AAF file for single WAV: {actual_path}")
            return True
        else:
            logger(f"Error: Failed to parse WAV file: {wav_path}")
            return False

    # Directory case
    wav_directory = wav_path
    # Track whether user explicitly requested an output path BEFORE setting defaults
    explicit_output_requested = bool(output_aaf_file)
    
    # Resolve output path/root before scanning so we can emit logs even if no WAVs are found
    wav_basename = os.path.basename(os.path.normpath(wav_directory))
    if not output_aaf_file:
        # Default: place outputs next to WAV directory under an 'AAFs/<basename>' folder
        wav_parent = os.path.dirname(os.path.normpath(wav_directory))
        aafs_dir = os.path.join(wav_parent, 'AAFs')
        try:
            os.makedirs(aafs_dir, exist_ok=True)
        except Exception:
            pass
        output_aaf_file = os.path.join(aafs_dir, wav_basename, f"{wav_basename}.aaf")
        logger(f"Using default AAF filepath: {output_aaf_file}")
        parent_output_dir = aafs_dir
    elif os.path.isdir(output_aaf_file):
        parent_output_dir = output_aaf_file
        logger(f"Using output folder: {output_aaf_file}")
    else:
        parent_output_dir = os.path.dirname(output_aaf_file) if output_aaf_file else None
    try:
        if parent_output_dir:
            os.makedirs(parent_output_dir, exist_ok=True)
    except Exception:
        pass
    aafs_output_root = os.path.join(parent_output_dir, wav_basename)
    try:
        os.makedirs(aafs_output_root, exist_ok=True)
    except Exception:
        pass

    # Build directory maps for WAVs and non-WAV audio files
    dir_wav_map = {}
    dir_nonwav_map = {}
    nonwav_exts = {'.aiff', '.aif', '.sd2'}
    for dirpath, dirnames, filenames in os.walk(wav_directory):
        wavs = []
        nonwavs = []
        for f in filenames:
            p = os.path.join(dirpath, f)
            ext = os.path.splitext(f)[1].lower()
            if ext == '.wav':
                wavs.append(p)
            elif ext in nonwav_exts:
                nonwavs.append(p)
        if wavs:
            dir_wav_map[dirpath] = wavs
        if nonwavs:
            dir_nonwav_map[dirpath] = nonwavs

    # If no WAVs found anywhere, write error
    if not dir_wav_map:
        logger(f"Error: No WAV files found in the directory '{wav_directory}'.")
        return False

    # Decide single-file vs per-subdir (only single-file if user explicitly chose an output path)
    user_requested_single_file = bool(explicit_output_requested and output_aaf_file and not os.path.isdir(output_aaf_file))

    if user_requested_single_file:
        if cancel_event is not None and cancel_event.is_set():
            logger("Cancelled before processing top-level WAVs.")
            return False
        top_level_wavs = [p for p in dir_wav_map.get(wav_directory, [])]
        if not top_level_wavs:
            logger(f"Error: No WAV files found in the directory '{wav_directory}'.")
            return False
        logger(f"Creating individual AAFs for top-level WAVs in: {wav_directory}")
        
        # Create individual AAF files for each WAV
        success_count = 0
        for wav_file in top_level_wavs:
            metadata = parse_wav_metadata(wav_file, fps)
            if metadata:
                wav_basename = os.path.splitext(os.path.basename(wav_file))[0]
                individual_aaf_path = os.path.join(os.path.dirname(output_aaf_file), f"{wav_basename}.aaf")
                actual_path = create_embedded_aaf_file(wav_file, metadata, individual_aaf_path, fps)
                if actual_path:
                    if output_paths is not None:
                        output_paths.append(actual_path)
                    success_count += 1
        
        if success_count > 0:
            logger(f"Successfully created {success_count} AAF files")
            return True
        else:
            logger("No valid WAVs to include in AAF.")
            return False

    # Per-subdirectory AAFs - create individual AAF files for each WAV
    logger("Creating individual AAFs per subdirectory…")
    cancelled_mid_run = False
    for dirpath, wavs in sorted(dir_wav_map.items()):
        if cancel_event is not None and cancel_event.is_set():
            logger("Cancelled. Stopping before next subdirectory.")
            cancelled_mid_run = True
            break
        rel = os.path.relpath(dirpath, wav_directory)
        target_dir = aafs_output_root if rel == '.' else os.path.join(aafs_output_root, rel)
        try:
            os.makedirs(target_dir, exist_ok=True)
        except Exception:
            pass
        
        # Create individual AAF for each WAV file in this directory
        for wav_file in wavs:
            metadata = parse_wav_metadata(wav_file, fps)
            if metadata:
                wav_basename = os.path.splitext(os.path.basename(wav_file))[0]
                out_file = os.path.join(target_dir, f"{wav_basename}.aaf")
                actual_path = create_embedded_aaf_file(wav_file, metadata, out_file, fps)
                if actual_path:
                    if output_paths is not None:
                        output_paths.append(actual_path)
                    logger(f"Wrote AAF: {actual_path}")
                    
    if cancelled_mid_run:
        logger("Cancelled. Some AAFs may have been created before stopping.")
        return False
    logger("Done.")
    return True

def launch_gui():
    """Launch a minimal Tkinter GUI for selecting inputs and running conversion."""
    if tk is None:
        print("GUI components are unavailable. Ensure tkinter is installed.")
        return

    root = tk.Tk()
    root.title("WAVsToAAF")
    root.geometry("680x520")

    # Variables
    wav_var = tk.StringVar()
    out_var = tk.StringVar()
    fps_var = tk.StringVar(value="24")
    last_outputs = { 'paths': [] }
    cancel_event = threading.Event()

    def log(msg):
        log_text.configure(state='normal')
        log_text.insert('end', str(msg) + "\n")
        log_text.see('end')
        log_text.configure(state='disabled')
        # Capture generated AAF paths from log lines to enable Reveal button
        try:
            s = str(msg)
            markers = ["Successfully created AAF file for single WAV:", "Successfully created AAF file:", "Wrote AAF:"]
            for m in markers:
                if s.startswith(m):
                    path = s.split(m, 1)[1].strip()
                    if path:
                        # If it ends with '.aaf', store it; otherwise ignore
                        if path.lower().endswith('.aaf'):
                            if path not in last_outputs['paths']:
                                last_outputs['paths'].append(path)
                            try:
                                # Show and enable the button when first output appears
                                if not open_btn.winfo_ismapped():
                                    open_btn.pack(side='left', padx=(8,0))
                                open_btn.configure(state='normal')
                            except Exception:
                                pass
                    break
        except Exception:
            pass

    def browse_wav_file():
        path = filedialog.askopenfilename(title="Select WAV file",
                                          filetypes=[("WAV Files", "*.wav"), ("All Files", "*.*")])
        if path:
            wav_var.set(path)

    def browse_wav_dir():
        path = filedialog.askdirectory(title="Select WAV directory")
        if path:
            wav_var.set(path)

    def browse_out():
        path = filedialog.askdirectory(title="Select output folder")
        if path:
            out_var.set(path)

    def run_clicked():
        # Parse FPS (allow non-integer frame rates like 23.976 or 29.97)
        try:
            fps = float(fps_var.get().strip() or "24")
            if fps <= 0:
                raise ValueError
        except Exception:
            messagebox.showwarning("Invalid FPS", "FPS must be a positive number (e.g. 24 or 23.976). Using 24.")
            fps = 24.0
        wavp = wav_var.get().strip() or None
        outp = out_var.get().strip() or None

        if not wavp:
            messagebox.showerror("Missing input", "Please select a WAV file or directory.")
            return

        if not AAF_AVAILABLE:
            messagebox.showerror("Missing Dependency", "pyaaf2 library not available.\n\nPlease install it using:\npip install pyaaf2")
            return

        # Run in a thread to keep UI responsive
        cancel_event.clear()
        try:
            run_btn.configure(state='disabled')
            cancel_btn.configure(state='normal')
        except Exception:
            pass
        def worker():
            log("Starting AAF creation…")
            last_outputs['paths'].clear()
            ok = run_conversion(None, wavp, outp, fps=fps, logger=log, cancel_event=cancel_event, output_paths=last_outputs['paths'])
            # Update UI from main thread
            def finish_ui():
                try:
                    run_btn.configure(state='normal')
                    cancel_btn.configure(state='disabled')
                except Exception:
                    pass
                if ok:
                    messagebox.showinfo("Done", "AAF creation completed.")
                else:
                    # If user canceled, show a clear cancellation message
                    if cancel_event.is_set():
                        messagebox.showinfo("Cancelled", "AAF creation canceled. Some AAFs may have already been created.")
                    else:
                        messagebox.showerror("Error", "AAF creation failed. Check the log for details.")
            try:
                root.after(0, finish_ui)
            except Exception:
                finish_ui()

        threading.Thread(target=worker, daemon=True).start()

    def cancel_clicked():
        cancel_event.set()
        log("Cancellation requested…")

    def clear_log():
        log_text.configure(state='normal')
        log_text.delete('1.0', 'end')
        log_text.configure(state='disabled')

    def open_output_location():
        # If the user set an Output Folder, prioritize opening that location
        outp = (out_var.get().strip() or '')
        wavp = (wav_var.get().strip() or '')
        if outp:
            try:
                folder = outp if os.path.isdir(outp) else os.path.dirname(outp)
                subprocess.run(['open', folder], check=False)
                return
            except Exception:
                pass
        # Otherwise, prefer revealing the last created AAF file if tracked
        paths = last_outputs.get('paths') or []
        if paths:
            target = paths[-1]  # last created AAF
            try:
                subprocess.run(['open', '-R', target], check=False)
                return
            except Exception:
                pass
        # Fallback: open expected folder based on inputs
        try:
            if os.path.isfile(wavp):
                wb = os.path.splitext(os.path.basename(wavp))[0]
                folder = os.path.join(os.path.dirname(wavp), 'AAFs', wb)
            else:
                wb = os.path.basename(os.path.normpath(wavp))
                folder = os.path.join(os.path.dirname(os.path.normpath(wavp)), 'AAFs', wb)
            subprocess.run(['open', folder], check=False)
        except Exception:
            messagebox.showwarning("Open Location", "Could not open the AAF location.")

    # Layout
    frm = ttk.Frame(root, padding=12)
    frm.pack(fill='both', expand=True)

    # Check AAF availability and show warning if not available
    if not AAF_AVAILABLE:
        warning_frame = ttk.Frame(frm)
        warning_frame.grid(row=0, column=0, columnspan=3, sticky='ew', pady=(0, 8))
        warning_label = ttk.Label(warning_frame, text="⚠️ pyaaf2 library not found. Please install it using: pip install pyaaf2", 
                                 foreground="red", font=('TkDefaultFont', 9))
        warning_label.pack()

    # WAV
    row_offset = 1 if not AAF_AVAILABLE else 0
    ttk.Label(frm, text="WAV file or directory").grid(row=row_offset, column=0, sticky='w')
    wav_entry = ttk.Entry(frm, textvariable=wav_var, width=60)
    wav_entry.grid(row=row_offset+1, column=0, columnspan=2, sticky='we', pady=(1,0))
    wav_btns = ttk.Frame(frm)
    wav_btns.grid(row=row_offset+1, column=2, sticky='w', pady=0)
    ttk.Button(wav_btns, text="File…", command=browse_wav_file).grid(row=0, column=0, padx=(0,4), pady=0)
    ttk.Button(wav_btns, text="Folder…", command=browse_wav_dir).grid(row=0, column=1, pady=0)

    # Output
    ttk.Label(frm, text="Output Folder for AAFs").grid(row=row_offset+2, column=0, sticky='w', pady=(6,0))
    out_entry = ttk.Entry(frm, textvariable=out_var, width=60)
    out_entry.grid(row=row_offset+3, column=0, columnspan=2, sticky='we', pady=(1,0))
    ttk.Button(frm, text="Browse…", command=browse_out).grid(row=row_offset+3, column=2, sticky='w', pady=0)

    # FPS
    fps_row = ttk.Frame(frm)
    fps_row.grid(row=row_offset+4, column=0, columnspan=3, sticky='w', pady=(6,8))
    ttk.Label(fps_row, text="FPS:").pack(side='left')
    ttk.Entry(fps_row, textvariable=fps_var, width=8).pack(side='left', padx=(4,0))
    ttk.Label(fps_row, text="(default 24)").pack(side='left', padx=(6,0))

    # Action buttons
    buttons_row = ttk.Frame(frm)
    buttons_row.grid(row=row_offset+5, column=0, columnspan=3, sticky='w', pady=(0,8))
    run_btn = ttk.Button(buttons_row, text="Run", command=run_clicked)
    run_btn.pack(side='left')
    cancel_btn = ttk.Button(buttons_row, text="Cancel", command=cancel_clicked, state='disabled')
    cancel_btn.pack(side='left', padx=(8,0))
    open_btn = ttk.Button(buttons_row, text="Open AAF Location", command=open_output_location, state='disabled')
    # Keep hidden until an AAF is generated
    try:
        open_btn.pack_forget()
    except Exception:
        pass

    # Log area with clear button
    log_header = ttk.Frame(frm)
    log_header.grid(row=row_offset+6, column=0, columnspan=3, sticky='ew', pady=(0,2))
    ttk.Label(log_header, text="Output Log").pack(side='left')
    ttk.Button(log_header, text="Clear", command=clear_log, width=8).pack(side='right')

    log_text = ScrolledText(frm, height=16, state='disabled')
    log_text.grid(row=row_offset+7, column=0, columnspan=3, sticky='nsew')
    frm.rowconfigure(row_offset+7, weight=1)

    # Copyright, website, and version labels below log
    copyright_font = (None, 10)
    copyright_lbl = ttk.Label(frm, text="© Jason Brodkey", font=copyright_font, anchor='w', justify='left')
    copyright_lbl.grid(row=row_offset+8, column=0, sticky='w', pady=(4,0))

    def open_website(event=None):
        import webbrowser
        webbrowser.open_new_tab('https://www.editcandy.com')

    website_lbl = ttk.Label(frm, text="www.editcandy.com", font=copyright_font, foreground="#4ea3ff", cursor="hand2")
    website_lbl.grid(row=row_offset+8, column=0, columnspan=3, pady=(4,0))
    website_lbl.bind("<Button-1>", open_website)
    
    version_lbl = ttk.Label(frm, text=f"v{__version__}", font=copyright_font, anchor='e', justify='right')
    version_lbl.grid(row=row_offset+8, column=2, sticky='e', pady=(4,0))
    
    frm.columnconfigure(0, weight=1)

    root.mainloop()

def main():
    """Main function to orchestrate the WAV to AAF conversion."""
    global UCS_MAPPING
    
    # Handle --version flag
    if len(sys.argv) > 1 and sys.argv[1] in ('--version', '-v'):
        print(f"WAVsToAAF v{__version__}")
        return
    
    # Check AAF library availability
    if not AAF_AVAILABLE:
        print("Error: pyaaf2 library not available. Please install it using: pip install pyaaf2")
        return
    
    # Try to find UCS CSV in the script directory first
    try:
        script_dir = os.path.dirname(os.path.realpath(__file__))
    except Exception:
        script_dir = os.getcwd()
    
    default_name = 'data/UCS_v8.2.1_Full_List.csv'
    # Prefer bundled resource if present (PyInstaller) else script directory
    default_ucs = resource_path(default_name)
    ucs_csv_file = default_ucs if os.path.isfile(default_ucs) else None
    
    # Only use built-in UCS; do not prompt. Fallback to resource scan; otherwise abort.
    if not ucs_csv_file:
        base_dir = getattr(sys, "_MEIPASS", script_dir)
        try:
            for fname in os.listdir(base_dir):
                if fname.lower().endswith('.csv') and 'ucs' in fname.lower():
                    ucs_csv_file = os.path.join(base_dir, fname)
                    break
        except Exception:
            pass
    if not ucs_csv_file:
        print("Error: Built-in UCS source not found.")
        return
    else:
        if getattr(sys, 'frozen', False):
            print("Using built-in UCS source")
        else:
            print(f"Using UCS CSV: {ucs_csv_file}")
    
    # Prompt user for input (WAV directory, FPS, and output file)
    raw_wav = input("Enter the path to the WAV directory or single WAV file: ")
    raw_fps = input("Enter the frame rate (FPS) for the AAF file (default is 24): ").strip()
    raw_out = input("Enter the path for the output AAF file (RETURN for default): ")
    
    # Parse FPS input (allow non-integer frame rates)
    try:
        fps = float(raw_fps) if raw_fps else 24.0
        if fps <= 0:
            print("Invalid FPS value. Using default of 24.")
            fps = 24.0
    except ValueError:
        print(f"Invalid FPS value '{raw_fps}'. Using default of 24.")
        fps = 24.0

    # Treat empty responses as missing (so they don't resolve to cwd via abspath)
    wav_path = sanitize_path(raw_wav) if raw_wav and raw_wav.strip() else None
    output_aaf_file = sanitize_path(raw_out) if raw_out and raw_out.strip() else None

    # Validate input path
    if not wav_path:
        print("Error: No WAV file or directory provided.")
        return
    
    # Check if input is a single file or directory
    is_single_file = os.path.isfile(wav_path)
    is_directory = os.path.isdir(wav_path)
    
    if not is_single_file and not is_directory:
        print(f"Error: Path does not exist or is not a file/directory: {wav_path}")
        return
    
    # Handle single file case
    if is_single_file:
        if not wav_path.lower().endswith('.wav'):
            print(f"Error: File is not a WAV file: {wav_path}")
            return
        
        wav_basename = os.path.splitext(os.path.basename(wav_path))[0]
        
        # Default AAFs folder is subdirectory next to the WAV file's parent
        wav_parent = os.path.dirname(wav_path)
        aafs_dir = os.path.join(wav_parent, 'AAFs')
        
        if not output_aaf_file:
            output_aaf_file = os.path.join(aafs_dir, wav_basename, f"{wav_basename}.aaf")
            print(f"Using default AAF filepath: {output_aaf_file}")
        elif os.path.isdir(output_aaf_file):
            output_aaf_file = os.path.join(output_aaf_file, f"{wav_basename}.aaf")
            print(f"Output path is a directory. Using default file: {output_aaf_file}")
        
        # Ensure output directory exists
        try:
            os.makedirs(os.path.dirname(output_aaf_file), exist_ok=True)
        except Exception:
            pass
        
        # Load UCS mapping
        UCS_MAPPING = load_ucs_mapping(ucs_csv_file)
        if not UCS_MAPPING:
            print("Error: Failed to load UCS mapping. Ensure the CSV file is valid.")
            return
        
        # Process single WAV file
        print(f"Processing single WAV file: {wav_path}")
        metadata = parse_wav_metadata(wav_path, fps)

        if metadata:
            actual_path = create_embedded_aaf_file(wav_path, metadata, output_aaf_file, fps)
            if actual_path:
                print(f"Successfully created AAF file for single WAV: {actual_path}")
        else:
            print(f"Error: Failed to parse WAV file: {wav_path}")
            if SKIP_LOG:
                print(f"Error details: {SKIP_LOG[-1]}")
        return
    
    # Directory handling
    wav_directory = wav_path
    wav_basename = os.path.basename(os.path.normpath(wav_directory))
    wav_parent = os.path.dirname(os.path.normpath(wav_directory))
    aafs_dir = os.path.join(wav_parent, 'AAFs')
    
    # Ensure the AAFs directory exists
    try:
        os.makedirs(aafs_dir, exist_ok=True)
    except Exception:
        pass

    if not output_aaf_file:
        output_aaf_file = os.path.join(aafs_dir, wav_basename, f"{wav_basename}.aaf")
        print(f"Using default AAF filepath: {output_aaf_file}")
    elif os.path.isdir(output_aaf_file):
        output_aaf_file = os.path.join(output_aaf_file, f"{wav_basename}.aaf")
        print(f"Output path is a directory. Using default file: {output_aaf_file}")

    # Load UCS mapping
    UCS_MAPPING = load_ucs_mapping(ucs_csv_file)
    if not UCS_MAPPING:
        print("Error: Failed to load UCS mapping. Ensure the CSV file is valid.")
        return

    # Run conversion
    success = run_conversion(ucs_csv_file, wav_directory, output_aaf_file, fps)
    if success:
        print("AAF creation completed successfully.")
    else:
        print("AAF creation failed.")

if __name__ == "__main__":
    # Auto-launch GUI when frozen (packaged app) unless --no-gui is specified
    # Or when --gui is explicitly requested
    is_frozen = getattr(sys, 'frozen', False)
    
    if "--gui" in sys.argv or (is_frozen and "--no-gui" not in sys.argv and tk is not None):
        launch_gui()
    elif is_frozen and tk is None:
        # In a packaged app with no tkinter available, show an error and exit
        import platform
        error_msg = "The GUI could not be loaded (tkinter is unavailable). Please re-download the app or contact support."
        
        try:
            if platform.system() == "Darwin":
                # On macOS, use osascript
                subprocess.run(["osascript", "-e", f'display alert "WAVsToAAF" message "{error_msg}" as critical buttons {"OK"}'], check=False)
            else:
                print(error_msg)
        except Exception:
            print(error_msg)
        
        sys.exit(1)
    else:
        main()