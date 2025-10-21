import wave
import os
import struct
import xml.etree.ElementTree as ET

def parse_wav_metadata(wav_file_path):
    """Extract metadata from a WAV file, including BEXT, XML, and INFO chunks."""
    metadata = {}
    try:
        # Open the WAV file using the wave module
        with wave.open(wav_file_path, 'rb') as wav_file:
            duration = round(wav_file.getnframes() / wav_file.getframerate(), 2)
            # Calculate SMPTE 24fps timecode for duration
            frames = int((duration % 1) * 24)
            seconds = int(duration) % 60
            minutes = (int(duration) // 60) % 60
            hours = int(duration) // 3600
            smpte_duration = f"{hours:02}:{minutes:02}:{seconds:02}:{frames:02}"

            # Determine Tracks field based on Channels
            channels = wav_file.getnchannels()
            tracks = "A1" if channels == 1 else "A1A2" if channels == 2 else f"A1A{channels}"

            metadata.update({
                "Name": sanitize_string(os.path.basename(wav_file_path)),
                "Tape": "",  # Blank for all entries
                "Start": "00:00:00:00",  # Default value
                "End": smpte_duration,  # SMPTE 24fps timecode
                "Tracks": tracks,  # A1 for mono, A1A2 for stereo
                "AudioFormat": "WAV",
                "Filename": sanitize_string(os.path.basename(wav_file_path)),
                "Channels": channels,
                "Sample Width": wav_file.getsampwidth(),
                "Frame Rate": wav_file.getframerate(),
                "Number of Frames": wav_file.getnframes(),
                "Duration": duration,
            })

        # Parse BEXT, XML, and INFO chunks
        with open(wav_file_path, 'rb') as f:
            data = f.read()
            metadata.update(parse_bext_chunk(data))
            metadata.update(parse_xml_chunk(data))
            metadata.update(parse_info_chunk(data))

    except EOFError:
        print(f"Warning: The file '{wav_file_path}' appears to be corrupted or incomplete. Skipping.")
    except wave.Error as e:
        print(f"Warning: Error reading WAV file '{wav_file_path}': {e}. Skipping.")
    except Exception as e:
        print(f"Warning: Unexpected error while processing '{wav_file_path}': {e}. Skipping.")
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
                "Description": description,
                "Originator": originator,
                "Originator Reference": originator_ref,
                "Origination Date": origination_date,
                "Origination Time": origination_time,
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
            root = ET.fromstring(xml_data)
            for elem in root.iter():
                tag = elem.tag.split('}')[-1]  # Remove namespace
                text = sanitize_string(elem.text.strip() if elem.text else None)
                if text:
                    xml_metadata[tag] = text
    except Exception as e:
        print(f"Error parsing XML chunk: {e}")
    return xml_metadata

def parse_info_chunk(data):
    """Parse the INFO chunk from the WAV file."""
    info_metadata = {}
    try:
        # Locate the INFO chunk
        info_start = data.find(b'LIST')
        if info_start != -1:
            # Check if it's an INFO chunk
            if data[info_start + 8:info_start + 12] == b'INFO':
                # Start reading INFO chunk entries
                info_start += 12
                while info_start + 8 <= len(data):  # Ensure there's enough data for chunk ID and size
                    # Read the chunk ID (4 bytes)
                    chunk_id = data[info_start:info_start + 4].decode('ascii', errors='ignore').strip()
                    # Read the chunk size (4 bytes, little-endian)
                    chunk_size = struct.unpack('<I', data[info_start + 4:info_start + 8])[0]
                    # Ensure there's enough data for the chunk data
                    if info_start + 8 + chunk_size > len(data):
                        print(f"Warning: INFO chunk '{chunk_id}' is incomplete. Skipping.")
                        break
                    # Read the chunk data
                    chunk_data = data[info_start + 8:info_start + 8 + chunk_size].decode('ascii', errors='ignore').strip()
                    # Add to metadata
                    info_metadata[chunk_id] = sanitize_string(chunk_data)
                    # Move to the next chunk
                    info_start += 8 + chunk_size
    except Exception as e:
        print(f"Error parsing INFO chunk: {e}")
    return info_metadata

def sanitize_string(value):
    """Remove null bytes and non-printable characters from a string."""
    if isinstance(value, str):
        return value.replace("\x00", "").strip()
    return value


def sanitize_path(path_str):
    """Normalize a path string coming from user input.

    - Strips surrounding single or double quotes if present
    - Expands ~ and environment variables
    - Returns absolute path
    """
    if path_str is None:
        return path_str
    # Remove surrounding whitespace then any enclosing quotes
    s = path_str.strip()
    # Strip matching surrounding quotes (single or double)
    if (s.startswith("'") and s.endswith("'")) or (s.startswith('"') and s.endswith('"')):
        s = s[1:-1]
    # Expand user and vars and make absolute
    s = os.path.expanduser(os.path.expandvars(s))
    try:
        s = os.path.abspath(s)
    except Exception:
        # Fallback: return as-is after expansions
        pass
    return s

def create_ale_file(metadata_list, output_file_path):
    """Create an ALE file from a list of metadata dictionaries."""
    # Define required columns for ALE
    required_columns = ["Name", "Tape", "Start", "End", "Tracks", "AudioFormat"]

    # Collect all unique metadata keys from the metadata list
    all_columns = set(required_columns)
    for metadata in metadata_list:
        all_columns.update(metadata.keys())

    # Exclude unwanted columns
    excluded_columns = {"Origination Date", "Origination Time", "Sample Width", "Duration", "Channels"}
    all_columns = [col for col in all_columns if col not in excluded_columns]

    # Ensure required columns are first and in order
    all_columns = list(required_columns) + [col for col in all_columns if col not in required_columns]

    # Ensure all metadata entries have the required columns
    for metadata in metadata_list:
        for column in all_columns:
            if column not in metadata:
                metadata[column] = "N/A"  # Default value for missing columns

    # Open the output ALE file
    with open(output_file_path, 'w') as ale_file:
        # Write ALE header
        ale_file.write("Heading\n")
        ale_file.write("FIELD_DELIM\tTABS\n")
        ale_file.write("VIDEO_FORMAT\t1080\n")
        ale_file.write("AUDIO_FORMAT\t48khz\n")       
        ale_file.write("FPS\t24\n")       
        ale_file.write("\n")
        ale_file.write("Column\n")
        ale_file.write("\t".join(all_columns) + "\n")
        ale_file.write("\n")
        ale_file.write("Data\n")
        
        # Write metadata rows
        for metadata in metadata_list:
            row = [str(metadata.get(column, "N/A")) for column in all_columns]
            ale_file.write("\t".join(row) + "\n")
    print(f"ALE file created at: {output_file_path}")

def main():
    # Input WAV file directory
    wav_directory = input("Enter the directory containing WAV files: ")
    output_ale_file = input("Enter the output ALE file path: ")

    # Normalize user-provided paths (strip quotes, expand ~, make absolute)
    wav_directory = sanitize_path(wav_directory)
    output_ale_file = sanitize_path(output_ale_file)

    # Basic validation
    if not wav_directory:
        print("Error: No WAV directory provided.")
        return

    if not os.path.isdir(wav_directory):
        print(f"Error: WAV directory does not exist: {wav_directory}")
        return

    # Ensure output path is a valid file path
    if output_ale_file and os.path.isdir(output_ale_file):
        output_ale_file = os.path.join(output_ale_file, "output.ale")
        print(f"Output path is a directory. Using default file: {output_ale_file}")

    # Parse metadata from all WAV files in the directory
    metadata_list = []
    for file_name in os.listdir(wav_directory):
        if file_name.lower().endswith('.wav'):
            wav_file_path = os.path.join(wav_directory, file_name)
            metadata = parse_wav_metadata(wav_file_path)
            if metadata:
                metadata_list.append(metadata)

    if metadata_list:
        # Create ALE file
        create_ale_file(metadata_list, output_ale_file)
    else:
        print("No valid WAV files found in the directory.")

if __name__ == "__main__":
    main()