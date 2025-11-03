"""
This script creates Avid Log Exchange (ALE) files by parsing metadata from SFX WAV files.
It extracts metadata from:
- Standard WAV properties
- Broadcast audio metadata (BEXT)
- Embedded XML
- File naming conventions (UCS categories)
 
It will generate one ALE per subdirectory of WAV files if the input is a directory
It will generate one ALE file with a single entry if the input is a single WAV file.

The resulting ALE file can be imported into Avid Media Composer to help catalog 
and organize audio files based on their metadata.

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
        log_path = os.path.join(tempfile.gettempdir(), 'WavToALE_gui_error.log')
        with open(log_path, 'a', encoding='utf-8') as _f:
            _f.write(f"[{ts}] tkinter import failed:\n")
            _f.write(''.join(traceback.format_exception(_tk_err)))
            _f.write("\n")
    except Exception:
        pass

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
    """Remove null bytes, non-printable characters, tabs, newlines, and non-ASCII characters for strict ALE compatibility."""
    if value:
        # Replace tabs, newlines, and carriage returns with spaces first
        cleaned = value.replace('\t', ' ').replace('\n', ' ').replace('\r', ' ')
        # Remove non-printable characters
        cleaned = ''.join(char for char in cleaned if char.isprintable())
        # Remove non-ASCII characters for strict ALE compatibility (only allow ASCII 0-127)
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
    e.g., file.ale -> file_1.ale -> file_2.ale, etc.
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

def create_ale_file(metadata_list, output_file_path, fps=24):
    """Create an ALE file from the extracted metadata. Returns the actual path used."""
    if not metadata_list:
        print("Error: No metadata to write to ALE file.")
        return None

    # Check if file exists and get unique path if needed
    output_file_path = get_unique_filepath(output_file_path)

    # Required ALE columns (ensure these come first)
    # Note: "Color" column must come before "Name" per Avid ALE spec
    required_columns = ["Color", "Name", "Tape", "Start", "End", "Tracks", "AudioFormat"]

    # Collect all unique metadata keys from the metadata list
    all_columns = set(required_columns)
    for metadata in metadata_list:
        all_columns.update(metadata.keys())

    # Exclude unwanted internal columns
    excluded_columns = {"Origination Date", "Origination Time", "Sample Width", "Duration", "Channels"}
    all_columns = [col for col in all_columns if col not in excluded_columns]

    # Ensure required columns are first and in order
    all_columns = list(required_columns) + [col for col in sorted(all_columns) if col not in required_columns]

    # Ensure all metadata entries have every column
    for metadata in metadata_list:
        for column in all_columns:
            if column not in metadata:
                metadata[column] = ""

    # Write ALE with a conventional Heading/Column/Data structure
    try:
        tmp_path = output_file_path + '.tmp'
        with open(tmp_path, 'w', newline='', encoding='utf-8') as ale_file:
            ale_file.write("Heading\n")
            ale_file.write("FIELD_DELIM\tTABS\n")
            ale_file.write("VIDEO_FORMAT\t1080\n")
            ale_file.write("AUDIO_FORMAT\t48khz\n")
            ale_file.write(f"FPS\t{fps}\n")
            ale_file.write("\n")
            ale_file.write("Column\n")
            ale_file.write("\t".join(all_columns) + "\n")
            ale_file.write("\n")
            ale_file.write("Data\n")

            # Filter out any metadata entries that are empty (all columns blank/whitespace)
            for metadata in metadata_list:
                values = [str(metadata.get(column, "")).strip() for column in all_columns]
                if not any(values):
                    # skip entirely blank rows
                    continue
                ale_file.write("\t".join(values) + "\n")

        # Atomic replace
        try:
            os.replace(tmp_path, output_file_path)
        except Exception:
            # Best-effort cleanup
            try:
                os.remove(tmp_path)
            except Exception:
                pass
            raise

        print(f"Successfully created ALE file: {output_file_path}")
        return output_file_path

    except Exception as e:
        print(f"Error creating ALE file: {e}")
        return None

def run_conversion(ucs_csv_file, wav_path, output_ale_file, fps=24, logger=print, cancel_event: threading.Event | None = None, output_paths: list | None = None):
    """Run the conversion using existing logic without interactive prompts.

    Parameters:
    - ucs_csv_file: Optional path to UCS CSV. If None or invalid, attempt default lookup in script directory.
    - wav_path: Path to a single WAV file or a directory containing WAVs.
    - output_ale_file: Optional desired ALE output path; default location will be used if not provided.
    - fps: Integer FPS for ALE header.
    - logger: Function to consume log strings (defaults to print). GUI can pass a custom logger.
    - output_paths: Optional list to collect actual ALE file paths created (for GUI tracking).
    """
    global UCS_MAPPING
    
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
        default_name = 'UCS_v8.2.1_Full_List.csv'
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

    # Note: We'll create default ALEs folder(s) only when actually used (to avoid
    # creating stray 'ALEs' directories when a custom Output Folder is provided).

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
        if not output_ale_file:
            # Place default output inside a folder named after the WAV
            wav_parent = os.path.dirname(wav_path)
            ales_dir = os.path.join(wav_parent, 'ALEs')
            try:
                os.makedirs(ales_dir, exist_ok=True)
            except Exception:
                pass
            output_ale_file = os.path.join(ales_dir, wav_basename, f"{wav_basename}.ale")
            logger(f"Using default ALE filepath: {output_ale_file}")
        elif os.path.isdir(output_ale_file):
            output_ale_file = os.path.join(output_ale_file, f"{wav_basename}.ale")
            logger(f"Output path is a directory. Using default file: {output_ale_file}")
        try:
            os.makedirs(os.path.dirname(output_ale_file), exist_ok=True)
        except Exception:
            pass

        logger(f"Processing single WAV file: {wav_path}")
        metadata = parse_wav_metadata(wav_path, fps)
        if metadata:
            actual_path = create_ale_file([metadata], output_ale_file, fps)
            if actual_path:
                if output_paths is not None:
                    output_paths.append(actual_path)
                logger(f"Successfully created ALE file for single WAV: {actual_path}")
            return True
        else:
            logger(f"Error: Failed to parse WAV file: {wav_path}")
            # Write a skip log for single-file failures so issues are recorded on disk
            try:
                skip_log_path = output_ale_file + '.skip.log'
                total_processed = 1
                total_successful = 0
                total_skipped = 1
                # Count errors by type from the last SKIP_LOG entry if available
                error_counts = {}
                if SKIP_LOG:
                    last = SKIP_LOG[-1]
                    if '\t' in last:
                        error_type = last.split('\t', 1)[1].split(':')[0]
                        error_counts[error_type] = error_counts.get(error_type, 0) + 1
                with open(skip_log_path, 'w', encoding='utf-8') as f:
                    f.write("=" * 80 + "\n")
                    f.write("SKIP LOG SUMMARY\n")
                    f.write("=" * 80 + "\n")
                    f.write(f"Total files processed: {total_processed}\n")
                    f.write(f"Successfully parsed: {total_successful}\n")
                    f.write(f"Skipped (errors): {total_skipped}\n")
                    f.write("\n")
                    if error_counts:
                        f.write("Errors by type:\n")
                        for error_type, count in sorted(error_counts.items()):
                            f.write(f"  {error_type}: {count}\n")
                    f.write("=" * 80 + "\n\n")
                    f.write("DETAILED ERROR LOG\n")
                    f.write("-" * 80 + "\n")
                    if SKIP_LOG:
                        f.write(SKIP_LOG[-1] + '\n')
                    else:
                        f.write(f"{wav_path}\tError: Unknown parse failure\n")
                logger(f"Wrote skip log: {skip_log_path}")
            except Exception:
                pass
            return False

    # Directory case
    wav_directory = wav_path
    # Track whether user explicitly requested an output path BEFORE setting defaults
    # (affects single-file vs per-subdir behavior)
    explicit_output_requested = bool(output_ale_file)
    
    # Resolve output path/root before scanning so we can emit logs even if no WAVs are found
    wav_basename = os.path.basename(os.path.normpath(wav_directory))
    if not output_ale_file:
        # Default: place outputs next to WAV directory under an 'ALEs/<basename>' folder
        wav_parent = os.path.dirname(os.path.normpath(wav_directory))
        ales_dir = os.path.join(wav_parent, 'ALEs')
        try:
            os.makedirs(ales_dir, exist_ok=True)
        except Exception:
            pass
        output_ale_file = os.path.join(ales_dir, wav_basename, f"{wav_basename}.ale")
        logger(f"Using default ALE filepath: {output_ale_file}")
        parent_output_dir = ales_dir
    elif os.path.isdir(output_ale_file):
        # Treat provided path as an output root folder; do NOT convert to a file path
        parent_output_dir = output_ale_file
        logger(f"Using output folder: {output_ale_file}")
    else:
        parent_output_dir = os.path.dirname(output_ale_file) if output_ale_file else None
    try:
        if parent_output_dir:
            os.makedirs(parent_output_dir, exist_ok=True)
    except Exception:
        pass
    ales_output_root = os.path.join(parent_output_dir, wav_basename)
    try:
        os.makedirs(ales_output_root, exist_ok=True)
    except Exception:
        pass

    # Build directory maps for WAVs and non-WAV audio files to improve skip logging
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

    # If no WAVs found anywhere, optionally write a summary skip log for detected non-WAV audio
    if not dir_wav_map:
        total_nonwavs = sum(len(v) for v in dir_nonwav_map.values())
        if total_nonwavs:
            try:
                out_file = os.path.join(ales_output_root, f"{wav_basename}.ale")
                skip_log_path = out_file + '.skip.log'
                tmp_path = skip_log_path + '.tmp'
                with open(tmp_path, 'w', encoding='utf-8') as f:
                    f.write("=" * 80 + "\n")
                    f.write("SKIP LOG SUMMARY\n")
                    f.write("=" * 80 + "\n")
                    f.write("Total files processed: 0\n")
                    f.write("Successfully parsed: 0\n")
                    f.write(f"Skipped (errors): {total_nonwavs}\n")
                    f.write("\nErrors by type:\n  UnsupportedFormat: Non-WAV audio: {0}\n".format(total_nonwavs))
                    f.write("=" * 80 + "\n\n")
                    f.write("DETAILED ERROR LOG\n")
                    f.write("-" * 80 + "\n")
                    for dirpath, files in sorted(dir_nonwav_map.items()):
                        for p in files:
                            f.write(f"{p}\tUnsupportedFormat: Non-WAV audio\n")
                try:
                    os.replace(tmp_path, skip_log_path)
                except Exception:
                    try:
                        os.remove(tmp_path)
                    except Exception:
                        pass
                logger(f"Wrote skip log: {skip_log_path}")
            except Exception:
                pass
        logger(f"Error: No WAV files found in the directory '{wav_directory}'.")
        return False

    # Decide single-file vs per-subdir (only single-file if user explicitly chose an output path)
    user_requested_single_file = bool(explicit_output_requested and output_ale_file and not os.path.isdir(output_ale_file))

    if user_requested_single_file:
        if cancel_event is not None and cancel_event.is_set():
            logger("Cancelled before processing top-level WAVs.")
            return False
        top_level_wavs = [p for p in dir_wav_map.get(wav_directory, [])]
        if not top_level_wavs:
            logger(f"Error: No WAV files found in the directory '{wav_directory}'.")
            return False
        logger(f"Creating single ALE for top-level WAVs in: {wav_directory}")
        start_len = len(SKIP_LOG)
        # Record any top-level non-WAV audio as skipped
        for p in dir_nonwav_map.get(wav_directory, []):
            try:
                SKIP_LOG.append(f"{p}\tUnsupportedFormat: Non-WAV audio")
            except Exception:
                pass
        with ThreadPoolExecutor() as executor:
            # Pass fps through to parsing so SMPTE frame calc is accurate for non-integer rates
            metadata_list = list(executor.map(lambda p: parse_wav_metadata(p, fps), top_level_wavs))
        metadata_list = [m for m in metadata_list if m]
        if metadata_list:
            actual_path = create_ale_file(metadata_list, output_ale_file, fps)
            if actual_path:
                if output_paths is not None:
                    output_paths.append(actual_path)
                if actual_path != output_ale_file:
                    output_ale_file = actual_path  # Update for skip log filename

        if len(SKIP_LOG) > start_len:
            try:
                skip_log_path = output_ale_file + '.skip.log'
                skipped_entries = SKIP_LOG[start_len:]
                total_processed = len(top_level_wavs)
                total_skipped = len(skipped_entries)
                total_successful = len(metadata_list)
                error_counts = {}
                for entry in skipped_entries:
                    if '\t' in entry:
                        error_type = entry.split('\t', 1)[1].split(':')[0]
                        error_counts[error_type] = error_counts.get(error_type, 0) + 1
                tmp_path = skip_log_path + '.tmp'
                with open(tmp_path, 'w', encoding='utf-8') as f:
                    f.write("=" * 80 + "\n")
                    f.write("SKIP LOG SUMMARY\n")
                    f.write("=" * 80 + "\n")
                    f.write(f"Total files processed: {total_processed}\n")
                    f.write(f"Successfully parsed: {total_successful}\n")
                    f.write(f"Skipped (errors): {total_skipped}\n")
                    f.write("\n")
                    if error_counts:
                        f.write("Errors by type:\n")
                        for error_type, count in sorted(error_counts.items()):
                            f.write(f"  {error_type}: {count}\n")
                    f.write("=" * 80 + "\n\n")
                    f.write("DETAILED ERROR LOG\n")
                    f.write("-" * 80 + "\n")
                    for line in skipped_entries:
                        f.write(line + '\n')
                try:
                    os.replace(tmp_path, skip_log_path)
                except Exception:
                    try:
                        os.remove(tmp_path)
                    except Exception:
                        pass
                logger(f"Wrote skip log: {skip_log_path}")
            except Exception:
                pass
        if metadata_list:
            logger(f"Successfully created ALE file: {output_ale_file}")
            return True
        else:
            logger("No valid WAVs to include in ALE (see skip log).")
            return False

    # Per-subdirectory ALEs
    logger("Creating ALEs per subdirectory…")
    cancelled_mid_run = False
    for dirpath, wavs in sorted(dir_wav_map.items()):
        if cancel_event is not None and cancel_event.is_set():
            logger("Cancelled. Stopping before next subdirectory.")
            cancelled_mid_run = True
            break
        rel = os.path.relpath(dirpath, wav_directory)
        target_dir = ales_output_root if rel == '.' else os.path.join(ales_output_root, rel)
        try:
            os.makedirs(target_dir, exist_ok=True)
        except Exception:
            pass
        out_file = os.path.join(target_dir, f"{os.path.basename(dirpath)}.ale")
        start_len = len(SKIP_LOG)
        # Record any non-WAV audio in this directory as skipped
        for p in dir_nonwav_map.get(dirpath, []):
            try:
                SKIP_LOG.append(f"{p}\tUnsupportedFormat: Non-WAV audio")
            except Exception:
                pass
        with ThreadPoolExecutor() as executor:
            metadata_list = list(executor.map(lambda p: parse_wav_metadata(p, fps), wavs))
        metadata_list = [m for m in metadata_list if m]
        if metadata_list:
            actual_path = create_ale_file(metadata_list, out_file, fps)
            if actual_path:
                if output_paths is not None:
                    output_paths.append(actual_path)
                logger(f"Wrote ALE: {actual_path}")
        # Write skip log if any entries were added (including non-WAVs or parse failures),
        # even if we didn't produce an ALE file for this directory
        if len(SKIP_LOG) > start_len:
            try:
                skip_log_path = out_file + '.skip.log'
                skipped_entries = SKIP_LOG[start_len:]
                total_processed = len(wavs)
                total_skipped = len(skipped_entries)
                total_successful = len(metadata_list)
                error_counts = {}
                for entry in skipped_entries:
                    if '\t' in entry:
                        error_type = entry.split('\t', 1)[1].split(':')[0]
                        error_counts[error_type] = error_counts.get(error_type, 0) + 1
                tmp_path = skip_log_path + '.tmp'
                with open(tmp_path, 'w', encoding='utf-8') as f:
                    f.write("=" * 80 + "\n")
                    f.write("SKIP LOG SUMMARY\n")
                    f.write("=" * 80 + "\n")
                    f.write(f"Total files processed: {total_processed}\n")
                    f.write(f"Successfully parsed: {total_successful}\n")
                    f.write(f"Skipped (errors): {total_skipped}\n")
                    f.write("\n")
                    if error_counts:
                        f.write("Errors by type:\n")
                        for error_type, count in sorted(error_counts.items()):
                            f.write(f"  {error_type}: {count}\n")
                    f.write("=" * 80 + "\n\n")
                    f.write("DETAILED ERROR LOG\n")
                    f.write("-" * 80 + "\n")
                    for line in skipped_entries:
                        f.write(line + '\n')
                try:
                    os.replace(tmp_path, skip_log_path)
                except Exception:
                    try:
                        os.remove(tmp_path)
                    except Exception:
                        pass
                logger(f"Wrote skip log: {skip_log_path}")
            except Exception:
                pass
    if cancelled_mid_run:
        logger("Cancelled. Some ALEs may have been created before stopping.")
        return False
    logger("Done.")
    return True

def launch_gui():
    """Launch a minimal Tkinter GUI for selecting inputs and running conversion."""
    if tk is None:
        print("GUI components are unavailable. Ensure tkinter is installed.")
        return

    root = tk.Tk()
    root.title("WAVsToALE")
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
        # Capture generated ALE paths from log lines to enable Reveal button
        try:
            s = str(msg)
            markers = ["Successfully created ALE file for single WAV:", "Successfully created ALE file:", "Wrote ALE:"]
            for m in markers:
                if s.startswith(m):
                    path = s.split(m, 1)[1].strip()
                    if path:
                        # If it ends with '.ale', store it; otherwise ignore
                        if path.lower().endswith('.ale'):
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

        # Run in a thread to keep UI responsive
        cancel_event.clear()
        try:
            run_btn.configure(state='disabled')
            cancel_btn.configure(state='normal')
        except Exception:
            pass
        def worker():
            log("Starting conversion…")
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
                    messagebox.showinfo("Done", "ALE creation completed.")
                else:
                    # If user canceled, show a clear cancellation message
                    if cancel_event.is_set():
                        messagebox.showinfo("Cancelled", "ALE creation canceled. Some ALEs may have already been created.")
                    else:
                        messagebox.showerror("Error", "ALE creation failed. Check the log for details.")
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
        # Otherwise, prefer revealing the last created ALE file if tracked
        paths = last_outputs.get('paths') or []
        if paths:
            target = paths[-1]  # last created ALE
            try:
                subprocess.run(['open', '-R', target], check=False)
                return
            except Exception:
                pass
        # Fallback: open expected folder based on inputs
        try:
            if os.path.isfile(wavp):
                wb = os.path.splitext(os.path.basename(wavp))[0]
                folder = os.path.join(os.path.dirname(wavp), 'ALEs', wb)
            else:
                wb = os.path.basename(os.path.normpath(wavp))
                folder = os.path.join(os.path.dirname(os.path.normpath(wavp)), 'ALEs', wb)
            subprocess.run(['open', folder], check=False)
        except Exception:
            messagebox.showwarning("Open Location", "Could not open the ALE location.")

    # Layout
    frm = ttk.Frame(root, padding=12)
    frm.pack(fill='both', expand=True)

    # WAV
    ttk.Label(frm, text="WAV file or directory").grid(row=0, column=0, sticky='w')
    wav_entry = ttk.Entry(frm, textvariable=wav_var, width=60)
    # Tiny positive top padding to nudge entry down for visual alignment
    wav_entry.grid(row=1, column=0, columnspan=2, sticky='we', pady=(1,0))
    # Place the buttons in a frame in the same row as the entry
    wav_btns = ttk.Frame(frm)
    wav_btns.grid(row=1, column=2, sticky='w', pady=0)
    ttk.Button(wav_btns, text="File…", command=browse_wav_file).grid(row=0, column=0, padx=(0,4), pady=0)
    ttk.Button(wav_btns, text="Folder…", command=browse_wav_dir).grid(row=0, column=1, pady=0)

    # Output
    ttk.Label(frm, text="Output Folder for ALES").grid(row=2, column=0, sticky='w', pady=(6,0))
    out_entry = ttk.Entry(frm, textvariable=out_var, width=60)
    # Mirror tiny top padding for consistent alignment
    out_entry.grid(row=3, column=0, columnspan=2, sticky='we', pady=(1,0))
    ttk.Button(frm, text="Browse…", command=browse_out).grid(row=3, column=2, sticky='w', pady=0)

    # FPS
    fps_row = ttk.Frame(frm)
    fps_row.grid(row=4, column=0, columnspan=3, sticky='w', pady=(6,8))
    ttk.Label(fps_row, text="FPS:").pack(side='left')
    ttk.Entry(fps_row, textvariable=fps_var, width=8).pack(side='left', padx=(4,0))
    ttk.Label(fps_row, text="(default 24)").pack(side='left', padx=(6,0))

    # Action buttons
    buttons_row = ttk.Frame(frm)
    buttons_row.grid(row=5, column=0, columnspan=3, sticky='w', pady=(0,8))
    run_btn = ttk.Button(buttons_row, text="Run", command=run_clicked)
    run_btn.pack(side='left')
    cancel_btn = ttk.Button(buttons_row, text="Cancel", command=cancel_clicked, state='disabled')
    cancel_btn.pack(side='left', padx=(8,0))
    open_btn = ttk.Button(buttons_row, text="Open ALE Location", command=open_output_location, state='disabled')
    # Keep hidden until an ALE is generated
    try:
        open_btn.pack_forget()
    except Exception:
        pass

    # Log area with clear button
    log_header = ttk.Frame(frm)
    log_header.grid(row=6, column=0, columnspan=3, sticky='ew', pady=(0,2))
    ttk.Label(log_header, text="Output Log").pack(side='left')
    ttk.Button(log_header, text="Clear", command=clear_log, width=8).pack(side='right')

    log_text = ScrolledText(frm, height=16, state='disabled')
    log_text.grid(row=7, column=0, columnspan=3, sticky='nsew')
    frm.rowconfigure(7, weight=1)

    # Copyright, website, and version labels below log
    copyright_font = (None, 10)
    copyright_lbl = ttk.Label(frm, text="© Jason Brodkey", font=copyright_font, anchor='w', justify='left')
    copyright_lbl.grid(row=8, column=0, sticky='w', pady=(4,0))

    def open_website(event=None):
        import webbrowser
        webbrowser.open_new_tab('https://www.editcandy.com')

    website_lbl = ttk.Label(frm, text="www.editcandy.com", font=copyright_font, foreground="#4ea3ff", cursor="hand2")
    website_lbl.grid(row=8, column=0, columnspan=3, pady=(4,0))
    website_lbl.bind("<Button-1>", open_website)
    
    version_lbl = ttk.Label(frm, text=f"v{__version__}", font=copyright_font, anchor='e', justify='right')
    version_lbl.grid(row=8, column=2, sticky='e', pady=(4,0))
    
    frm.columnconfigure(0, weight=1)

    root.mainloop()

def main():
    """Main function to orchestrate the WAV to ALE conversion."""
    global UCS_MAPPING
    
    # Handle --version flag
    if len(sys.argv) > 1 and sys.argv[1] in ('--version', '-v'):
        print(f"WAVsToALE v{__version__}")
        return
    
    # Try to find UCS CSV in the script directory first
    try:
        script_dir = os.path.dirname(os.path.realpath(__file__))
    except Exception:
        script_dir = os.getcwd()
    
    default_name = 'UCS_v8.2.1_Full_List.csv'
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
    raw_fps = input("Enter the frame rate (FPS) for the ALE file (default is 24): ").strip()
    raw_out = input("Enter the path for the output ALE file (RETURN for default): ")
    
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
    output_ale_file = sanitize_path(raw_out) if raw_out and raw_out.strip() else None

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
        
        # Set wav_directory to the parent directory for consistency
        wav_directory = os.path.dirname(wav_path)
        wav_basename = os.path.splitext(os.path.basename(wav_path))[0]
        single_wav_file = wav_path
        
        # Default ALEs folder is subdirectory next to the WAV file's parent
        wav_parent = os.path.dirname(wav_path)
        ales_dir = os.path.join(wav_parent, 'ALEs')
        
        if not output_ale_file:
            output_ale_file = os.path.join(ales_dir, wav_basename, f"{wav_basename}.ale")
            print(f"Using default ALE filepath: {output_ale_file}")
        elif os.path.isdir(output_ale_file):
            output_ale_file = os.path.join(output_ale_file, f"{wav_basename}.ale")
            print(f"Output path is a directory. Using default file: {output_ale_file}")
        
        # Ensure output directory exists
        try:
            os.makedirs(os.path.dirname(output_ale_file), exist_ok=True)
        except Exception:
            pass
        
        # Load UCS mapping
        UCS_MAPPING = load_ucs_mapping(ucs_csv_file)
        if not UCS_MAPPING:
            print("Error: Failed to load UCS mapping. Ensure the CSV file is valid.")
            return
        
        # Process single WAV file
        print(f"Processing single WAV file: {single_wav_file}")
        metadata = parse_wav_metadata(single_wav_file, fps)

        if metadata:
            actual_path = create_ale_file([metadata], output_ale_file, fps)
            if actual_path:
                print(f"Successfully created ALE file for single WAV: {actual_path}")
        else:
            print(f"Error: Failed to parse WAV file: {single_wav_file}")
            if SKIP_LOG:
                print(f"Error details: {SKIP_LOG[-1]}")
        return
    
    # Directory handling (existing code)
    wav_directory = wav_path
    # If user didn't provide an output path, default to subdirectory next to WAV directory
    wav_basename = os.path.basename(os.path.normpath(wav_directory))
    # Default ALEs folder is subdirectory next to the WAV directory
    wav_parent = os.path.dirname(os.path.normpath(wav_directory))
    ales_dir = os.path.join(wav_parent, 'ALEs')
    # Ensure the ALEs directory exists
    try:
        os.makedirs(ales_dir, exist_ok=True)
    except Exception:
        pass

    if not output_ale_file:
        output_ale_file = os.path.join(ales_dir, wav_basename, f"{wav_basename}.ale")
        print(f"Using default ALE filepath: {output_ale_file}")
    elif os.path.isdir(output_ale_file):
        # If the provided output is a directory, place the named ALE inside it
        output_ale_file = os.path.join(output_ale_file, f"{wav_basename}.ale")
        print(f"Output path is a directory. Using default file: {output_ale_file}")

    # Load UCS mapping
    UCS_MAPPING = load_ucs_mapping(ucs_csv_file)
    if not UCS_MAPPING:
        print("Error: Failed to load UCS mapping. Ensure the CSV file is valid.")
        return

    # Inspect the provided WAV directory for subdirectories containing WAV files.
    # Behavior:
    # - If there are subdirectories with WAV files and the user did NOT explicitly
    #   request a single output file, create one ALE per subdirectory (named after
    #   the subdirectory) and place them in the same directory as the computed
    #   output file. Also create a root-level ALE for WAVs directly under the
    #   provided directory if present.
    # - If the user explicitly provided a single output file path, preserve the
    #   original behavior and write a single ALE containing all WAVs found only
    #   at the top-level of the provided directory.

    # Recursively walk the WAV directory and group WAV files by directory.
    # We'll create one ALE per directory that contains WAV files.
    dir_wav_map = {}
    for dirpath, dirnames, filenames in os.walk(wav_directory):
        wavs = [os.path.join(dirpath, f) for f in filenames if f.lower().endswith('.wav')]
        if wavs:
            dir_wav_map[dirpath] = wavs

    # Determine the directory to place per-subdir ALEs
    # If user explicitly provided an output file, use its parent; otherwise use ALEs folder
    explicit_output_requested = bool(output_ale_file)
    parent_output_dir = os.path.dirname(output_ale_file) if explicit_output_requested else ales_dir
    try:
        os.makedirs(parent_output_dir, exist_ok=True)
    except Exception:
        pass

    # Create a subfolder named after the provided WAV directory to hold all generated ALEs
    ales_output_root = os.path.join(parent_output_dir, wav_basename)
    try:
        os.makedirs(ales_output_root, exist_ok=True)
    except Exception:
        pass

    # Was the user asking for a single explicit output file? If they provided a non-directory
    # output path, treat it as an explicit single-file request and keep the old behavior.
    user_requested_single_file = bool(raw_out and raw_out.strip() and not os.path.isdir(raw_out))

    if user_requested_single_file:
        # Single-file behavior: collect only top-level WAVs (not recursive)
        top_level_wavs = [p for p in dir_wav_map.get(wav_directory, [])]
        if not top_level_wavs:
            print(f"Error: No WAV files found in the directory '{wav_directory}'.")
            return

        start_len = len(SKIP_LOG)
        with ThreadPoolExecutor() as executor:
            metadata_list = list(executor.map(lambda p: parse_wav_metadata(p, fps), top_level_wavs))
        metadata_list = [m for m in metadata_list if m]

        create_ale_file(metadata_list, output_ale_file, fps)
        if len(SKIP_LOG) > start_len:
            try:
                skip_log_path = output_ale_file + '.skip.log'
                skipped_entries = SKIP_LOG[start_len:]
                total_processed = len(top_level_wavs)
                total_skipped = len(skipped_entries)
                total_successful = len(metadata_list)
                
                # Count errors by type
                error_counts = {}
                for entry in skipped_entries:
                    if '\t' in entry:
                        error_type = entry.split('\t', 1)[1].split(':')[0]
                        error_counts[error_type] = error_counts.get(error_type, 0) + 1
                
                with open(skip_log_path, 'w', encoding='utf-8') as f:
                    f.write("=" * 80 + "\n")
                    f.write("SKIP LOG SUMMARY\n")
                    f.write("=" * 80 + "\n")
                    f.write(f"Total files processed: {total_processed}\n")
                    f.write(f"Successfully parsed: {total_successful}\n")
                    f.write(f"Skipped (errors): {total_skipped}\n")
                    f.write("\n")
                    if error_counts:
                        f.write("Errors by type:\n")
                        for error_type, count in sorted(error_counts.items()):
                            f.write(f"  {error_type}: {count}\n")
                    f.write("=" * 80 + "\n")
                    f.write("\n")
                    f.write("DETAILED ERROR LOG\n")
                    f.write("-" * 80 + "\n")
                    for line in skipped_entries:
                        f.write(line + '\n')
            except Exception:
                pass

    else:
        # Recursive behavior: create an ALE for every directory that contains WAVs
        if not dir_wav_map:
            print(f"Error: No WAV files found in the directory '{wav_directory}'.")
            return

        for dirpath, wavs in sorted(dir_wav_map.items()):
            # Determine a mirrored output directory under ales_output_root
            rel = os.path.relpath(dirpath, wav_directory)
            if rel == '.':
                target_dir = ales_output_root
            else:
                target_dir = os.path.join(ales_output_root, rel)
            try:
                os.makedirs(target_dir, exist_ok=True)
            except Exception:
                pass

            out_file = os.path.join(target_dir, f"{os.path.basename(dirpath)}.ale")

            start_len = len(SKIP_LOG)
            with ThreadPoolExecutor() as executor:
                metadata_list = list(executor.map(lambda p: parse_wav_metadata(p, fps), wavs))
            metadata_list = [m for m in metadata_list if m]

            if metadata_list:
                actual_path = create_ale_file(metadata_list, out_file, fps)
                if actual_path and actual_path != out_file:
                    out_file = actual_path  # Update for skip log filename
                # Write per-ALE skip log entries
                if len(SKIP_LOG) > start_len:
                    try:
                        skip_log_path = out_file + '.skip.log'
                        skipped_entries = SKIP_LOG[start_len:]
                        total_processed = len(wavs)
                        total_skipped = len(skipped_entries)
                        total_successful = len(metadata_list)
                        
                        # Count errors by type
                        error_counts = {}
                        for entry in skipped_entries:
                            if '\t' in entry:
                                error_type = entry.split('\t', 1)[1].split(':')[0]
                                error_counts[error_type] = error_counts.get(error_type, 0) + 1
                        
                        with open(skip_log_path, 'w', encoding='utf-8') as f:
                            f.write("=" * 80 + "\n")
                            f.write("SKIP LOG SUMMARY\n")
                            f.write("=" * 80 + "\n")
                            f.write(f"Total files processed: {total_processed}\n")
                            f.write(f"Successfully parsed: {total_successful}\n")
                            f.write(f"Skipped (errors): {total_skipped}\n")
                            f.write("\n")
                            if error_counts:
                                f.write("Errors by type:\n")
                                for error_type, count in sorted(error_counts.items()):
                                    f.write(f"  {error_type}: {count}\n")
                            f.write("=" * 80 + "\n")
                            f.write("\n")
                            f.write("DETAILED ERROR LOG\n")
                            f.write("-" * 80 + "\n")
                            for line in skipped_entries:
                                f.write(line + '\n')
                    except Exception:
                        pass

if __name__ == "__main__":
    # Auto-launch GUI when frozen (packaged app) unless --no-gui is specified
    # Or when --gui is explicitly requested
    is_frozen = getattr(sys, 'frozen', False)
    
    if "--gui" in sys.argv or (is_frozen and "--no-gui" not in sys.argv and tk is not None):
        launch_gui()
    elif is_frozen and tk is None:
        # In a packaged app with no tkinter available, show an error and exit
        # Don't fallback to CLI mode because there's no stdin in windowed apps
        import platform
        error_msg = "The GUI could not be loaded (tkinter is unavailable). Please re-download the app or contact support."
        
        try:
            if platform.system() == "Windows":
                # On Windows, use a message box
                import ctypes
                ctypes.windll.user32.MessageBoxW(0, error_msg, "WAVsToALE Error", 0x10)
            elif platform.system() == "Darwin":
                # On macOS, use osascript
                subprocess.run(["osascript", "-e", f'display alert "WAVsToALE" message "{error_msg}" as critical buttons {"OK"}'], check=False)
            else:
                # On Linux, try zenity or notify-send
                try:
                    subprocess.run(["zenity", "--error", f"--text={error_msg}"], check=False)
                except FileNotFoundError:
                    try:
                        subprocess.run(["notify-send", "WAVsToALE Error", error_msg], check=False)
                    except FileNotFoundError:
                        print(error_msg)
        except Exception:
            print(error_msg)
        
        # Exit instead of falling back to CLI mode
        sys.exit(1)
    else:
        main()