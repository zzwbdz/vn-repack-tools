#!/usr/bin/env python3
"""
VSD Pack/Unpack Tool - GUI Batch Edition
"""

import sys
import struct
import os
import argparse
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog

# ==========================================
# 核心处理逻辑 (Core Logic)
# ==========================================

def pack_vsd(input_path, output_path, skip_bytes=0):
    """将 MPG 视频封包为 VSD 格式"""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"未找到输入文件: {input_path}")
    
    with open(input_path, 'rb') as f:
        video_data = f.read()
    
    with open(output_path, 'wb') as f:
        # 写入标识符 'VSD1'
        f.write(b'VSD1')
        # 写入 skip bytes 长度 (小端序 4字节)
        f.write(struct.pack('<I', skip_bytes))
        # 写入填充字节
        if skip_bytes > 0:
            f.write(b'\x00' * skip_bytes)
        # 写入视频数据
        f.write(video_data)
    
    print(f"成功封包: {Path(input_path).name} -> {Path(output_path).name}")

def unpack_vsd(input_path, output_path):
    """将 VSD 格式解包为 MPG 视频"""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"未找到输入文件: {input_path}")
        
    with open(input_path, 'rb') as f:
        # 1. 验证头部标识符
        magic = f.read(4)
        if magic != b'VSD1':
            raise ValueError(f"文件格式错误或不是 VSD1 格式")
            
        # 2. 读取 skip bytes 长度 (小端序 4字节)
        skip_bytes_data = f.read(4)
        if len(skip_bytes_data) < 4:
            raise ValueError("文件头部数据损坏")
            
        skip_bytes = struct.unpack('<I', skip_bytes_data)[0]
        
        # 3. 跳过填充字节
        f.seek(skip_bytes, os.SEEK_CUR)
        
        # 4. 读取实际的视频数据
        video_data = f.read()
        
    with open(output_path, 'wb') as f_out:
        f_out.write(video_data)
        
    print(f"成功解包: {Path(input_path).name} -> {Path(output_path).name} (跳过了 {skip_bytes} 字节)")

# ==========================================
# GUI 流程控制 (GUI Workflow)
# ==========================================

def run_gui_batch_pack():
    """图形化批量 封包(MPG->VSD) 流程"""
    input_dir = filedialog.askdirectory(title="选择包含 .mpg 文件的文件夹 (封包)")
    if not input_dir:
        return

    skip_bytes = simpledialog.askinteger("设置", "请输入填充字节数 (Skip Bytes):", initialvalue=0, minvalue=0)
    if skip_bytes is None:
        return

    input_path = Path(input_dir)
    output_path = input_path / "vsd_output"
    files = list(input_path.glob("*.mpg"))
    
    if not files:
        messagebox.showinfo("提示", f"在目录中未找到任何 .mpg 文件：\n{input_dir}")
        return

    output_path.mkdir(parents=True, exist_ok=True)
    success_count, error_count = 0, 0

    for file in files:
        target_file = output_path / (file.stem + ".vsd")
        try:
            pack_vsd(str(file), str(target_file), skip_bytes)
            success_count += 1
        except Exception as e:
            print(f"处理 {file.name} 出错: {e}")
            error_count += 1

    messagebox.showinfo("处理完成", 
                        f"封包任务结束！\n\n成功: {success_count} 个\n失败: {error_count} 个\n保存位置: {output_path}")

def run_gui_batch_unpack():
    """图形化批量 解包(VSD->MPG) 流程"""
    input_dir = filedialog.askdirectory(title="选择包含 .vsd 文件的文件夹 (解包)")
    if not input_dir:
        return

    input_path = Path(input_dir)
    output_path = input_path / "mpg_output"
    files = list(input_path.glob("*.vsd"))
    
    if not files:
        messagebox.showinfo("提示", f"在目录中未找到任何 .vsd 文件：\n{input_dir}")
        return

    output_path.mkdir(parents=True, exist_ok=True)
    success_count, error_count = 0, 0

    for file in files:
        target_file = output_path / (file.stem + ".mpg")
        try:
            unpack_vsd(str(file), str(target_file))
            success_count += 1
        except Exception as e:
            print(f"解包 {file.name} 出错: {e}")
            error_count += 1

    messagebox.showinfo("处理完成", 
                        f"解包任务结束！\n\n成功: {success_count} 个\n失败: {error_count} 个\n保存位置: {output_path}")

def main():
    if len(sys.argv) == 1:
        # GUI 模式
        root = tk.Tk()
        root.withdraw()
        
        # 弹窗让用户选择是打包还是解包
        choice = messagebox.askyesnocancel(
            "选择操作", 
            "请选择你需要执行的批量操作：\n\n[ 是 ] = 批量解包 (VSD -> MPG)\n[ 否 ] = 批量封包 (MPG -> VSD)\n[取消] = 退出"
        )
        
        if choice is True:
            run_gui_batch_unpack()
        elif choice is False:
            run_gui_batch_pack()
        return

    # 命令行模式保留
    parser = argparse.ArgumentParser(description='Pack and unpack AI5WIN engine VSD video files')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    # ... 在这里可以补全你原有的命令行 parser 参数
    pass 

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        print(error_msg)
        if len(sys.argv) == 1:
            tk.Tk().withdraw()
            messagebox.showerror("程序崩溃", error_msg)