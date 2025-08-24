import os
import ctypes

# 定义获取桌面路径的函数
def get_desktop_path():
    CSIDL_DESKTOP = 0x0000
    buf = ctypes.create_unicode_buffer(1024)
    ctypes.windll.shell32.SHGetFolderPathW(None, CSIDL_DESKTOP, None, 0, buf)
    return buf.value

# 定义统计文件夹中文件数量的函数
def count_files_in_folder(folder_path):
    file_count = 0
    try:
        for root, dirs, files in os.walk(folder_path):
            file_count += len(files)
    except PermissionError:
        print(f"没有权限访问文件夹: {folder_path}")
    return file_count

# 定义统计桌面文件夹中文件数量的函数
def count_files_in_desktop_folders():
    desktop_path = get_desktop_path()
    total_file_count = 0
    for item in os.listdir(desktop_path):
        item_path = os.path.join(desktop_path, item)
        if os.path.isdir(item_path):
            total_file_count += count_files_in_folder(item_path)
    return total_file_count

# 主函数
def main():
    try:
        result = count_files_in_desktop_folders()
        return f"当前操作系统用户桌面所有文件夹（包含隐藏文件）中的文件数量为: {result}"
    except Exception as e:
        return f"发生错误: {str(e)}"
