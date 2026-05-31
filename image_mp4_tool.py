import os
import subprocess
import json
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path

# --- 配置区 ---
IMG_EXTS = ('.png', '.jpg', '.jpeg', '.bmp', '.webp')

def select_folder(title="请选择文件夹"):
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    root.attributes("-topmost", True) # 确保窗口在最前面
    path = filedialog.askdirectory(title=title)
    root.destroy()
    return Path(path) if path else None

def select_file(title="请选择文件", filetypes=None):
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    path = filedialog.askopenfilename(title=title, filetypes=filetypes)
    root.destroy()
    return Path(path) if path else None

def save_file(title="保存文件", defaultextension=".mp4"):
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    path = filedialog.asksaveasfilename(title=title, defaultextension=defaultextension, 
                                       filetypes=[("Video", "*.mp4")])
    root.destroy()
    return Path(path) if path else None

def merge_images():
    print("\n[状态] 等待选择图片文件夹...")
    src_dir = select_folder("第一步：选择包含图片的原始文件夹")
    if not src_dir: return

    img_list = sorted([f for f in src_dir.glob("*") if f.suffix.lower() in IMG_EXTS])
    if not img_list:
        print("错误: 文件夹内没图！")
        return

    print("[状态] 等待设置导出视频路径...")
    output_path = save_file("第二步：设置导出的无损 MP4 位置")
    if not output_path: return

    fps = input("第三步：请输入帧率 (默认 60): ") or "60"

    # 生成映射文件
    mapping_data = [img.name for img in img_list]
    mapping_file = output_path.with_name(output_path.stem + "_mapping.json")
    with open(mapping_file, 'w', encoding='utf-8') as f:
        json.dump(mapping_data, f, indent=4, ensure_ascii=False)

    # FFmpeg 逻辑
    list_file = src_dir / "temp_ffmpeg_list.txt"
    with open(list_file, 'w', encoding='utf-8') as f:
        for img in img_list:
            f.write(f"file '{img.as_posix()}'\n")
            f.write(f"duration {1/float(fps)}\n")

    print(f"[*] 正在无损压制: {output_path.name}")
    cmd = [
        'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
        '-i', str(list_file),
        '-c:v', 'libx264rgb', '-crf', '0', '-pix_fmt', 'rgb24',
        str(output_path)
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print(f"\n[OK] 成功！\n视频: {output_path}\nJSON: {mapping_file}")
    except Exception as e:
        print(f"\n[Error] 失败: {e}")
    finally:
        if list_file.exists(): list_file.unlink()

def extract_images():
    print("\n[状态] 等待选择处理后的视频...")
    video_path = select_file("第一步：选择 Lada 处理完的 MP4", [("Video", "*.mp4;*.avi;*.mkv")])
    if not video_path: return

    print("[状态] 等待选择 JSON 映射文件...")
    mapping_path = select_file("第二步：选择对应的 _mapping.json 文件", [("JSON", "*.json")])
    if not mapping_path: return

    print("[状态] 等待选择导出图片目录...")
    output_dir = select_folder("第三步：选择图片还原保存的文件夹")
    if not output_dir: return

    with open(mapping_path, 'r', encoding='utf-8') as f:
        original_names = json.load(f)

    print("[*] 正在提取帧并还原名称...")
    temp_pattern = str(output_dir / "temp_%06d.png")
    subprocess.run(['ffmpeg', '-y', '-i', str(video_path), '-f', 'image2', temp_pattern], 
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    temp_files = sorted(output_dir.glob("temp_*.png"))
    rename_count = 0
    for i, temp_file in enumerate(temp_files):
        if i < len(original_names):
            target_path = output_dir / original_names[i]
            if target_path.exists(): target_path.unlink()
            temp_file.rename(target_path)
            rename_count += 1
    
    print(f"\n[OK] 还原完成，共处理 {rename_count} 张图片。")

def main():
    while True:
        print("\n" + "■" * 40)
        print("   Lada 工作流辅助工具 (UI 选择版)")
        print("■" * 40)
        print(" 1. [封包] 图片 -> 无损 MP4 (+映射表)")
        print(" 2. [解包] 视频 -> 还原原始文件名图片")
        print(" q. 退出 (Exit)")
        print("-" * 40)
        
        choice = input("请输入选项: ").lower()
        if choice == '1':
            merge_images()
        elif choice == '2':
            extract_images()
        elif choice == 'q':
            break
        else:
            print("无效输入！")

if __name__ == "__main__":
    main()