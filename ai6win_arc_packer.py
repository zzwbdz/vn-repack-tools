import os
import struct
import sys

def encode_filename(name):
    name_bytes = name.encode('cp932')
    name_buf = bytearray(0x104)
    name_buf[:len(name_bytes)] = name_bytes
    key = len(name_bytes) + 1
    for i in range(len(name_bytes)):
        name_buf[i] = (name_buf[i] + key) & 0xFF
        key -= 1
    return name_buf

def pack_ai6win_arc(input_dir, output_arc):
    files = []
    for root, _, filenames in os.walk(input_dir):
        for fn in filenames:
            relpath = os.path.relpath(os.path.join(root, fn), input_dir).replace('\\', '/')
            files.append(relpath)
    count = len(files)
    index_size = count * (0x104 + 12)
    data_offset = 4 + index_size
    index_entries = []
    file_datas = []
    offset = data_offset
    for name in files:
        with open(os.path.join(input_dir, name.replace('/', os.sep)), 'rb') as f:
            data = f.read()
        size = len(data)
        name_enc = encode_filename(name)
        entry = name_enc
        entry += struct.pack('>I', size)  # Size (大端)
        entry += struct.pack('>I', size)  # UnpackedSize (大端, 无压缩)
        entry += struct.pack('>I', offset)  # Offset (大端)
        index_entries.append(entry)
        file_datas.append(data)
        offset += size
    with open(output_arc, 'wb') as f:
        f.write(struct.pack('<I', count))
        for entry in index_entries:
            f.write(entry)
        for data in file_datas:
            f.write(data)
    print(f'打包完成: {output_arc} ({count} 个文件)')

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('用法: python ai6win_arc_packer.py <输入文件夹> <输出.arc>')
    else:
        pack_ai6win_arc(sys.argv[1], sys.argv[2])