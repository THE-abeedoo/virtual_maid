import os

def find_largest_folder(root_dir):
    if not isinstance(root_dir, str):
        return "Error: The input should be a string representing a directory path."
    if not os.path.exists(root_dir):
        return f"Error: The directory {root_dir} does not exist."
    largest_folder = None
    max_size = 0
    for root, dirs, files in os.walk(root_dir):
        for dir in dirs:
            dir_path = os.path.join(root, dir)
            try:
                total_size = 0
                for dir_root, _, dir_files in os.walk(dir_path):
                    for file in dir_files:
                        file_path = os.path.join(dir_root, file)
                        total_size += os.path.getsize(file_path)
                if total_size > max_size:
                    max_size = total_size
                    largest_folder = dir_path
            except Exception as e:
                print(f"Error processing {dir_path}: {e}")
    if largest_folder is None:
        return "No folders found in the specified directory."
    return largest_folder


def main(root_dir):
    return find_largest_folder(root_dir)
