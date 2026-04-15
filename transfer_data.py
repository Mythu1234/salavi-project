
import os
import sys
import json
import subprocess
import shutil
import re

# 1. Cấu hình đường dẫn
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_PATH = os.path.join(BASE_DIR, 'CSKH_04', 'settings.py')
MODELS_PATH = os.path.join(BASE_DIR, 'orders', 'models.py')
BACKUP_SETTINGS = os.path.join(BASE_DIR, 'CSKH_04', 'settings_backup_transfer.py')
BACKUP_MODELS = os.path.join(BASE_DIR, 'orders', 'models_backup_transfer.py')
JSON_FILE = os.path.join(BASE_DIR, 'data_backup.json')

def run_command(cmd_list):
    print(f"Executing: {' '.join(cmd_list)}")
    my_env = os.environ.copy()
    my_env["PYTHONIOENCODING"] = "utf-8"
    my_env["PYTHONUTF8"] = "1"
    
    result = subprocess.run(cmd_list, capture_output=True, text=True, encoding='utf-8', env=my_env)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return False
    return True

def main():
    print("--- BẮT ĐẦU QUY TRÌNH CHUYỂN DỮ LIỆU (V2 - SỬA LỖI LỆCH MODEL) ---")

    # BƯỚC 1: Backup và sửa Settings + Models để khớp với SQLite
    print("\n[Bước 1] Đang cấu hình tạm thời Settings và Models để khớp với SQLite...")
    shutil.copy(SETTINGS_PATH, BACKUP_SETTINGS)
    shutil.copy(MODELS_PATH, BACKUP_MODELS)
    
    # Sửa Settings sang SQLite
    with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    new_db_config = "\nDATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': BASE_DIR / 'db.sqlite3'}}\n"
    pattern = re.compile(r'DATABASES\s*=\s*{.*?}', re.DOTALL)
    if not pattern.search(content):
         pattern = re.compile(r'DATABASES\s*=\s*{\s*\'default\':\s*dj_database_url\.parse.*?}', re.DOTALL)
    modified_settings = pattern.sub(f"# {pattern.search(content).group(0)}\n{new_db_config}", content)
    with open(SETTINGS_PATH, 'w', encoding='utf-8') as f:
        f.write(modified_settings)

    # Sửa Models: Tạm thời bỏ MaCTDH để quay về mặc định 'id'
    with open(MODELS_PATH, 'r', encoding='utf-8') as f:
        m_content = f.read()
    # Tìm dòng MaCTDH = models.AutoField(primary_key=True) và comment nó lại
    m_modified = m_content.replace('MaCTDH = models.AutoField(primary_key=True)', '# MaCTDH = models.AutoField(primary_key=True)')
    with open(MODELS_PATH, 'w', encoding='utf-8') as f:
        f.write(m_modified)

    # BƯỚC 2: Export dữ liệu
    print("\n[Bước 2] Đang trích xuất dữ liệu từ SQLite...")
    success = run_command([
        sys.executable, 'manage.py', 'dumpdata', 
        '--exclude', 'contenttypes', 
        '--exclude', 'auth.Permission', 
        '--exclude', 'admin', 
        '--exclude', 'sessions', 
        '-o', 'data_backup.json'
    ])
    
    # KHÔI PHỤC NGAY LẬP TỨC
    print("\n[Bước 2.5] Khôi phục lại trạng thái Model và Settings cho PostgreSQL...")
    shutil.move(BACKUP_SETTINGS, SETTINGS_PATH)
    shutil.move(BACKUP_MODELS, MODELS_PATH)
    
    if not success:
        print("!!! Thất bại ở bước Export. Dừng lại.")
        return

    # BƯỚC 3: Dọn dẹp dữ liệu (Data Cleaning)
    print("\n[Bước 3] Đang dọn dẹp dữ liệu lỗi (Sửa mã nhân viên không hợp lệ)...")
    try:
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        modified = False
        for obj in data:
            if obj['model'] == 'cskh.tinnhantuvan':
                if obj['fields'].get('MaNV') == "Nhân viên":
                    obj['fields']['MaNV'] = None
                    modified = True
            
        if modified:
            with open(JSON_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print("--- Đã tự động sửa các bản ghi tin nhắn có mã nhân viên lỗi.")
    except Exception as e:
        print(f"!!! Lỗi khi dọn dẹp JSON: {e}")

    # BƯỚC 4: Nạp vào PostgreSQL
    print("\n[Bước 4] Đang nạp dữ liệu vào PostgreSQL...")
    success = run_command([sys.executable, 'manage.py', 'loaddata', 'data_backup.json'])

    if success:
        print("\n=== CHÚC MỪNG! DỮ LIỆU ĐÃ ĐƯỢC CHUYỂN THÀNH CÔNG ===")
    else:
        print("\n!!! Có lỗi khi nạp dữ liệu vào PostgreSQL.")

if __name__ == "__main__":
    main()
