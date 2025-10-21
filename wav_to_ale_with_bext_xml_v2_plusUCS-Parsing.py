import os
import csv
import wave
import io
import struct
from xml.etree.ElementTree import iterparse
from concurrent.futures import ThreadPoolExecutor

# Global UCS mapping dictionary
UCS_MAPPING = {}

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

def parse_wav_metadata(wav_file_path):
    """Extract metadata from a WAV file, including BEXT, XML, and INFO chunks."""
    metadata = {}
    try:
        # Use wave to get audio properties
        with wave.open(wav_file_path, 'rb') as wf:
            duration = round(wf.getnframes() / wf.getframerate(), 2)
            frames = int((duration % 1) * 24)
            seconds = int(duration) % 60
            minutes = (int(duration) // 60) % 60
            hours = int(duration) // 3600
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
                "Frame Rate": wf.getframerate(),
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

    except EOFError:
        print(f"EOFError: Unexpected end of file for {wav_file_path}")
    except wave.Error as e:
        print(f"WaveError: {e} for {wav_file_path}")
    except Exception as e:
        print(f"Error parsing WAV file {wav_file_path}: {e}")

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
    """Remove null bytes and non-printable characters from a string."""
    if value:
        return ''.join(char for char in value if char.isprintable())
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
    if (s.startswith("'") and s.endswith("'")) or (s.startswith('"') and s.endswith('"')):
        s = s[1:-1]
    s = os.path.expanduser(os.path.expandvars(s))
    try:
        s = os.path.abspath(s)
    except Exception:
        pass
    return s

def create_ale_file(metadata_list, output_file_path):
    """Create an ALE file from the extracted metadata."""
    if not metadata_list:
        print("Error: No metadata to write to ALE file.")
        return

    # Required ALE columns (ensure these come first)
    required_columns = ["Name", "Tape", "Start", "End", "Tracks", "AudioFormat"]

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
                metadata[column] = "N/A"

    # Write ALE with a conventional Heading/Column/Data structure
    try:
        with open(output_file_path, 'w', newline='', encoding='utf-8') as ale_file:
            ale_file.write("Heading\n")
            ale_file.write("FIELD_DELIM\tTABS\n")
            ale_file.write("VIDEO_FORMAT\t1080\n")
            ale_file.write("AUDIO_FORMAT\t48khz\n")
            ale_file.write("FPS\t24\n")
            ale_file.write("\n")
            ale_file.write("Column\n")
            ale_file.write("\t" + "\t".join(all_columns) + "\n")
            ale_file.write("\n")
            ale_file.write("Data\n")

            for metadata in metadata_list:
                row = [str(metadata.get(column, "N/A")) for column in all_columns]
                ale_file.write("\t".join(row) + "\n")

        print(f"Successfully created ALE file: {output_file_path}")

    except Exception as e:
        print(f"Error creating ALE file: {e}")

def main():
    """Main function to orchestrate the WAV to ALE conversion."""
    # Prompt user for input (UCS CSV first, then WAV directory)
    raw_ucs = input("Enter the path to the UCS CSV file: ")
    raw_wav = input("Enter the path to the WAV directory: ")
    raw_out = input("Enter the path for the output ALE file: ")

    # Treat empty responses as missing (so they don't resolve to cwd via abspath)
    ucs_csv_file = sanitize_path(raw_ucs) if raw_ucs and raw_ucs.strip() else None
    wav_directory = sanitize_path(raw_wav) if raw_wav and raw_wav.strip() else None
    output_ale_file = sanitize_path(raw_out) if raw_out and raw_out.strip() else None

    # If the UCS CSV wasn't provided, default to a UCS CSV in the script directory
    if not ucs_csv_file:
        try:
            script_dir = os.path.dirname(os.path.realpath(__file__))
        except Exception:
            script_dir = os.getcwd()

        # Preferred default filename
        default_name = 'UCS_v8.2.1_Full_List.csv'
        candidate = os.path.join(script_dir, default_name)
        if os.path.isfile(candidate):
            ucs_csv_file = candidate
            print(f"No UCS CSV provided. Using default in script directory: {ucs_csv_file}")
        else:
            # Fallback: look for any CSV in the script dir with 'ucs' in the name
            try:
                for fname in os.listdir(script_dir):
                    if fname.lower().endswith('.csv') and 'ucs' in fname.lower():
                        ucs_csv_file = os.path.join(script_dir, fname)
                        print(f"No UCS CSV provided. Found candidate in script dir: {ucs_csv_file}")
                        break
            except Exception:
                pass

    # Validate inputs (check UCS CSV first so mapping is available before processing directory)
    if not ucs_csv_file:
        print("Error: No UCS CSV file provided.")
        return
    if not os.path.isfile(ucs_csv_file):
        print(f"Error: UCS CSV file does not exist: {ucs_csv_file}")
        return
    if not wav_directory:
        print("Error: No WAV directory provided.")
        return
    if not os.path.isdir(wav_directory):
        print(f"Error: Directory does not exist: {wav_directory}")
        return
    # If user didn't provide an output path, default to <parent_of_wav_dir>/ALEs/<wav_dir_basename>.ale
    wav_basename = os.path.basename(os.path.normpath(wav_directory))
    parent_dir = os.path.dirname(os.path.normpath(wav_directory))
    ales_dir = os.path.join(parent_dir, 'ALEs')
    # Ensure the ALEs directory exists
    try:
        os.makedirs(ales_dir, exist_ok=True)
    except Exception:
        pass

    if not output_ale_file:
        output_ale_file = os.path.join(ales_dir, f"{wav_basename}.ale")
        print(f"No output path provided. Using default ALE file: {output_ale_file}")
    elif os.path.isdir(output_ale_file):
        # If the provided output is a directory, place the named ALE inside it
        output_ale_file = os.path.join(output_ale_file, f"{wav_basename}.ale")
        print(f"Output path is a directory. Using default file: {output_ale_file}")

    # Load UCS mapping
    global UCS_MAPPING
    UCS_MAPPING = load_ucs_mapping(ucs_csv_file)
    if not UCS_MAPPING:
        print("Error: Failed to load UCS mapping. Ensure the CSV file is valid.")
        return

    # Validate WAV directory and collect file paths
    if not os.path.isdir(wav_directory):
        print(f"Error: Directory '{wav_directory}' does not exist.")
        return

    wav_file_paths = [
        os.path.join(wav_directory, file_name)
        for file_name in os.listdir(wav_directory)
        if file_name.lower().endswith('.wav')
    ]

    if not wav_file_paths:
        print(f"Error: No WAV files found in the directory '{wav_directory}'.")
        return

    # Process WAV files and extract metadata
    metadata_list = []
    with ThreadPoolExecutor() as executor:
        metadata_list = list(executor.map(parse_wav_metadata, wav_file_paths))

    # Create ALE file
    create_ale_file(metadata_list, output_ale_file)

if __name__ == "__main__":
    main()