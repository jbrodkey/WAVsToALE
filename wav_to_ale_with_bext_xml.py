import wave
import os
import struct
import xml.etree.ElementTree as ET

def parse_wav_metadata(wav_file_path):
    """Extract metadata from a WAV file, including BEXT and XML chunks."""
    metadata = {}
    try:
        # Open the WAV file using the wave module
        with wave.open(wav_file_path, 'rb') as wav_file:
            metadata.update({
                "Filename": os.path.basename(wav_file_path),
                "Channels": wav_file.getnchannels(),
                "Sample Width": wav_file.getsampwidth(),
                "Frame Rate": wav_file.getframerate(),
                "Number of Frames": wav_file.getnframes(),
                "Duration (s)": round(wav_file.getnframes() / wav_file.getframerate(), 2),
            })

        # Parse BEXT and XML chunks
        with open(wav_file_path, 'rb') as f:
            data = f.read()
            metadata.update(parse_bext_chunk(data))
            metadata.update(parse_xml_chunk(data))

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
            description = data[bext_start:bext_start + 256].decode('ascii', errors='ignore').strip()
            originator = data[bext_start + 256:bext_start + 256 + 32].decode('ascii', errors='ignore').strip()
            originator_ref = data[bext_start + 288:bext_start + 288 + 32].decode('ascii', errors='ignore').strip()
            origination_date = data[bext_start + 320:bext_start + 320 + 10].decode('ascii', errors='ignore').strip()
            origination_time = data[bext_start + 330:bext_start + 330 + 8].decode('ascii', errors='ignore').strip()

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
                text = elem.text.strip() if elem.text else None
                if text:
                    xml_metadata[tag] = text
    except Exception as e:
        print(f"Error parsing XML chunk: {e}")
    return xml_metadata

def create_ale_file(metadata_list, output_file_path):
    """Create an ALE file from a list of metadata dictionaries."""
    with open(output_file_path, 'w') as ale_file:
        # Write ALE header
        ale_file.write("Heading\n")
        ale_file.write("FIELD_DELIM\tTABS\n")
        ale_file.write("VIDEO_FORMAT\t1080\n")
        ale_file.write("\n")
        ale_file.write("Column\n")
        ale_file.write("\t".join(metadata_list[0].keys()) + "\n")
        ale_file.write("\n")
        ale_file.write("Data\n")
        
        # Write metadata rows
        for metadata in metadata_list:
            ale_file.write("\t".join(str(value) for value in metadata.values()) + "\n")
    print(f"ALE file created at: {output_file_path}")

def main():
    # Input WAV file directory
    wav_directory = input("Enter the directory containing WAV files: ").strip()
    output_ale_file = input("Enter the output ALE file path: ").strip()

    # Ensure output path is a valid file path
    if os.path.isdir(output_ale_file):
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