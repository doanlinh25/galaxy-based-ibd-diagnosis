import os
def count_downloaded(n =0):
    if n == 0:
        dir = r"C:\Users\User\ppnckh\output_workflow\wf0"
    else:
        dir = r"C:\Users\User\ppnckh\output_workflow\wf1"
    all_items = os.listdir(dir)
    file_count = sum(1 for f in all_items if os.path.isfile(os.path.join(r"C:\Users\User\ppnckh\output_workflow", f)))

    return file_count

def delete_file(file_path):
    """
    Xóa file nếu tồn tại.
    """
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            print(f"Đã xóa file: {file_path}")
        except Exception as e:
            print(f"Lỗi khi xóa file {file_path}: {e}")
    else:
        print(f"File không tồn tại, không cần xóa: {file_path}")

def check_path_exists(path):
    """
    Kiểm tra xem folder hoặc file có tồn tại không
    """
    if os.path.exists(path):
        return True
    else:
        return False
