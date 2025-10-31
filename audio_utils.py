"""Audio utility functions for the lightsaber"""

import audiocore
import struct


def get_wav_duration(filename):
    """
    Extract duration from WAV file using CircuitPython audiocore.WaveFile for metadata
    and manual parsing for exact data chunk size
    Returns duration in seconds
    """
    try:
        file_path = f'sounds/{filename}.wav'
        
        # First, get audio properties using audiocore.WaveFile
        with open(file_path, 'rb') as f:
            wave_file = audiocore.WaveFile(f)
            sample_rate = wave_file.sample_rate
            bits_per_sample = wave_file.bits_per_sample
            channel_count = wave_file.channel_count
            
            # Now find the data chunk size by parsing the WAV header
            f.seek(0)
            riff_header = f.read(12)  # RIFF header
            if riff_header[:4] != b'RIFF' or riff_header[8:12] != b'WAVE':
                print(f"Warning: {filename}.wav is not a valid WAV file")
                return 1.0
            
            # Find data chunk
            while True:
                chunk_header = f.read(8)
                if len(chunk_header) < 8:
                    break
                chunk_id = chunk_header[:4]
                chunk_size = struct.unpack('<I', chunk_header[4:8])[0]
                
                if chunk_id == b'data':
                    # Found data chunk - calculate duration
                    bytes_per_sample = bits_per_sample // 8
                    bytes_per_frame = bytes_per_sample * channel_count
                    total_frames = chunk_size // bytes_per_frame
                    duration = total_frames / sample_rate
                    return duration
                else:
                    # Skip this chunk
                    f.seek(chunk_size, 1)
            
            print(f"Warning: Could not find data chunk in {filename}.wav")
            return 1.0
            
    except Exception as e:
        print(f"Error reading {filename}.wav: {e}")
        return 1.0  # Default fallback
