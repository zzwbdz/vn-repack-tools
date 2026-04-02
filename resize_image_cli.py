#! python3.12
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import freeze_support

# 尝试导入 Pillow 增强版
try:
    from PIL import Image, ImageFile
    # 容错：允许加载不完整的图片文件
    ImageFile.LOAD_TRUNCATED_IMAGES = True 
except ImportError:
    print("错误：未找到 Pillow 库。运行: py -3.12 -m pip install Pillow")
    input("按回车退出..."); sys.exit()

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def process_single_image(file_path, output_path, target_width):
    """
    单任务核心：包含极高的异常捕获逻辑
    """
    try:
        if not os.path.exists(file_path):
            return f"[跳过] 文件不存在: {os.path.basename(file_path)}"

        with Image.open(file_path) as img:
            # 记录原图参数
            orig_mode = img.mode
            orig_format = img.format
            orig_info = img.info
            orig_exif = img.getexif()

            # 计算比例
            w_percent = (target_width / float(img.size[0]))
            new_h = int((float(img.size[1]) * float(w_percent)))
            
            # 缩放处理 (LANCZOS 是最稳的算法)
            img_p = img.convert('RGBA') if orig_mode in ['P', '1'] else img
            img_res = img_p.resize((target_width, new_h), Image.Resampling.LANCZOS)
            
            # 严格模式还原
            if orig_mode in ['P', '1']:
                img_res = img_res.quantize(colors=256, method=2)
            elif img_res.mode != orig_mode:
                img_res = img_res.convert(orig_mode)

            # 组装元数据
            save_params = {'format': orig_format, 'exif': orig_exif}
            if 'dpi' in orig_info: save_params['dpi'] = orig_info['dpi']
            if 'icc_profile' in orig_info: save_params['icc_profile'] = orig_info['icc_profile']
            if 'transparency' in orig_info: save_params['transparency'] = orig_info['transparency']
            
            if orig_format in ['JPEG', 'JPG']:
                save_params['quality'] = 95
                save_params['subsampling'] = 0

            img_res.save(output_path, **save_params)
            return f"[成功] {os.path.basename(file_path)} ({orig_mode})"
    except Exception as e:
        return f"[错误] {os.path.basename(file_path)}: {str(e)}"

def run_gui():
    clear_screen()
    print("="*50)
    print("      批量缩放工具 Ultra版 (Python 3.12 优化)      ")
    print("="*50)

    # 路径获取与清洗
    raw_path = input("\n1. 请拖入文件夹路径: ").strip().strip('"').strip("'")
    if not os.path.isdir(raw_path):
        print("\n[失败] 路径无效或不是文件夹！")
        time.sleep(2)
        return

    # 分辨率获取
    raw_width = input("2. 请输入目标宽度 (像素): ").strip()
    if not raw_width.isdigit():
        print("\n[失败] 请输入有效的数字！")
        time.sleep(2)
        return
    
    target_width = int(raw_width)
    abs_path = os.path.abspath(raw_path)
    output_dir = os.path.join(abs_path, f"Resized_{target_width}px")

    # 扫描文件
    valid_exts = ('.jpg', '.jpeg', '.png', '.bmp', '.tga', '.webp', '.tiff')
    task_list = []
    for f in os.listdir(abs_path):
        if f.lower().endswith(valid_exts):
            task_list.append((os.path.join(abs_path, f), os.path.join(output_dir, f)))

    if not task_list:
        print("\n[提示] 该文件夹内没有支持的图片。")
        time.sleep(2)
        return

    print(f"\n检测到 {len(task_list)} 张图片。")
    if input(f"即将开始并行处理，确定执行？(y/n): ").lower() != 'y':
        return

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 计算最合理的进程数：核心数 vs 8 (防止高核机器内存溢出)
    worker_count = min(os.cpu_count() or 1, 8)
    
    start_t = time.time()
    print(f"\n[并行启动] 使用 {worker_count} 个逻辑核心加速中...\n")

    # 执行并行任务
    with ProcessPoolExecutor(max_workers=worker_count) as executor:
        futures = [executor.submit(process_single_image, t[0], t[1], target_width) for t in task_list]
        
        done_count = 0
        for future in as_completed(futures):
            done_count += 1
            print(f"[{done_count}/{len(task_list)}] {future.result()}")

    print("\n" + "="*50)
    print(f" 处理完成！耗时: {time.time()-start_t:.2f}s")
    print(f" 保存路径: {output_dir}")
    print("="*50)
    input("\n任务结束，按回车返回主菜单...")

if __name__ == '__main__':
    # 关键：Windows 运行 multiprocessing 必须调用这个
    freeze_support()
    
    # 终极保护：防止在导入时运行逻辑（多进程环境下）
    # 只有主进程会进入这个循环
    while True:
        try:
            run_gui()
        except KeyboardInterrupt:
            print("\n用户手动停止。")
            break
        except Exception as e:
            print(f"\n[严重崩溃] 系统错误: {e}")
            input("按回车尝试重启工具...")