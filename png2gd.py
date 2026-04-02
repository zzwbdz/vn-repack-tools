#!/usr/bin/env python3
"""
PNG to GD Format Converter
Converts PNG images to C4 engine GD format
"""

import sys
import struct
from PIL import Image
import argparse


class BitWriter:
    """Helper class for writing bits to a stream"""
    def __init__(self):
        self.buffer = bytearray()
        self.current_byte = 0
        self.bit_position = 0
    
    def write_bit(self, bit):
        """Write a single bit (MSB first)"""
        if bit:
            self.current_byte |= (1 << (7 - self.bit_position))
        self.bit_position += 1
        
        if self.bit_position == 8:
            self.buffer.append(self.current_byte)
            self.current_byte = 0
            self.bit_position = 0
    
    def write_bits(self, value, count):
        """Write multiple bits (MSB first)"""
        for i in range(count - 1, -1, -1):
            self.write_bit((value >> i) & 1)
    
    def flush(self):
        """Flush remaining bits"""
        if self.bit_position > 0:
            self.buffer.append(self.current_byte)
            self.current_byte = 0
            self.bit_position = 0
        return bytes(self.buffer)


def compress_lzss(data):
    """
    Compress data using LZSS-like algorithm (mode 'l')
    This is a simplified implementation
    """
    writer = BitWriter()
    frame = bytearray(0x10000)
    frame_pos = 1
    i = 0
    
    while i < len(data):
        # Try to find match in sliding window
        best_offset = 0
        best_length = 0
        max_length = min(18, len(data) - i)  # max count is 15 + 3 = 18
        
        if max_length >= 3:
            for length in range(3, max_length + 1):
                pattern = data[i:i + length]
                # Search in frame
                for offset in range(0x10000):
                    match = True
                    for j in range(length):
                        if frame[(offset + j) & 0xFFFF] != pattern[j]:
                            match = False
                            break
                    if match and length > best_length:
                        best_offset = offset
                        best_length = length
        
        if best_length >= 3:
            # Write match
            writer.write_bit(0)
            writer.write_bits(best_offset, 16)
            writer.write_bits(best_length - 3, 4)
            
            for j in range(best_length):
                frame[frame_pos & 0xFFFF] = data[i + j]
                frame_pos += 1
            i += best_length
        else:
            # Write literal
            writer.write_bit(1)
            writer.write_bits(data[i], 8)
            frame[frame_pos & 0xFFFF] = data[i]
            frame_pos += 1
            i += 1
    
    return writer.flush()


def compress_uncompressed(data):
    """No compression (mode 'b')"""
    return data


def write_gd2(output_path, pixels, width, height):
    """Write GD2 format (640x480)"""
    if width != 640 or height != 480:
        raise ValueError("GD2 format requires 640x480 resolution")
    
    with open(output_path, 'wb') as f:
        # Write header
        f.write(b'GD2\x1A')
        
        # Write dummy block data (3 * (width/10) * (height/10 - 1) bytes)
        block_count = (width // 10) * (height // 10 - 1)
        f.write(b'\x00' * (3 * block_count))
        
        # Write compression type
        f.write(b'b')  # uncompressed
        f.write(b'\x00')  # padding
        
        # Write pixel data
        f.write(pixels)


def write_gd3(output_path, pixels, width, height):
    """Write GD3 format (800x600)"""
    if width != 800 or height != 600:
        raise ValueError("GD3 format requires 800x600 resolution")
    
    with open(output_path, 'wb') as f:
        # Write header
        f.write(b'GD3\x1A')
        
        # Write dummy block data
        block_count = (width // 10) * (height // 10 - 1)
        f.write(b'\x00' * (3 * block_count))
        
        # Write compression type
        f.write(b'b')  # uncompressed
        f.write(b'\x00')  # padding
        
        # Write pixel data
        f.write(pixels)


def write_xex_gd(output_path, pixels):
    """Write XEX GD format (640x480, simplified header)"""
    with open(output_path, 'wb') as f:
        # Write compression type and marker
        f.write(b'l\x1A')
        
        # Write compressed pixel data
        compressed = compress_lzss(pixels)
        f.write(compressed)


def png_to_gd(input_path, output_path, format_type='auto'):
    """
    Convert PNG to GD format
    
    Args:
        input_path: Path to input PNG file
        output_path: Path to output GD file
        format_type: 'gd2' (640x480), 'gd3' (800x600), 'xex' (640x480), or 'auto'
    """
    # Load PNG
    img = Image.open(input_path)
    
    # Convert to RGB if necessary
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    width, height = img.size
    
    # Auto-detect format based on resolution
    if format_type == 'auto':
        if width == 640 and height == 480:
            format_type = 'gd2'
        elif width == 800 and height == 600:
            format_type = 'gd3'
        else:
            raise ValueError(f"Unsupported resolution: {width}x{height}. "
                           "GD format supports 640x480 (GD2) or 800x600 (GD3)")
    
    # Get pixel data in BGR24 format (flipped vertically)
    pixels = bytearray()
    for y in range(height - 1, -1, -1):  # Flip vertically
        for x in range(width):
            r, g, b = img.getpixel((x, y))
            pixels.extend([b, g, r])  # BGR order
    
    # Write in appropriate format
    if format_type == 'gd2':
        write_gd2(output_path, bytes(pixels), width, height)
    elif format_type == 'gd3':
        write_gd3(output_path, bytes(pixels), width, height)
    elif format_type == 'xex':
        if width != 640 or height != 480:
            raise ValueError("XEX format requires 640x480 resolution")
        write_xex_gd(output_path, bytes(pixels))
    else:
        raise ValueError(f"Unknown format type: {format_type}")
    
    print(f"Successfully converted {input_path} to {output_path} ({format_type})")


def main():
    parser = argparse.ArgumentParser(
        description='Convert PNG images to C4 engine GD format'
    )
    parser.add_argument('input', help='Input PNG file')
    parser.add_argument('output', help='Output GD file')
    parser.add_argument(
        '-f', '--format',
        choices=['auto', 'gd2', 'gd3', 'xex'],
        default='auto',
        help='Output format (default: auto-detect from resolution)'
    )
    
    args = parser.parse_args()
    
    try:
        png_to_gd(args.input, args.output, args.format)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()