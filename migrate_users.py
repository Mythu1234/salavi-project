import sqlite3
from datetime import datetime

def run():
    conn = sqlite3.connect('db.sqlite3', isolation_level=None)
    cursor = conn.cursor()

    # Thêm cột nếu chưa có (đã xử lý trước đó rồi nhưng cứ để cho an toàn)
    try:
        cursor.execute("ALTER TABLE accounts_khachhang ADD COLUMN user_id integer NULL REFERENCES auth_user(id);")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE accounts_nhanvien ADD COLUMN user_id integer NULL REFERENCES auth_user(id);")
    except sqlite3.OperationalError:
        pass

    # Lấy tài khoản cũ từ accounts_taikhoan
    cursor.execute("SELECT MaTK, TenDangNhap, MatKhau FROM accounts_taikhoan")
    taikhoans = cursor.fetchall()
    
    # Check max id trong auth_user
    cursor.execute("SELECT MAX(id) FROM auth_user")
    max_id = cursor.fetchone()[0]
    next_id = (max_id or 0) + 1
    
    tk_to_user = {}
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("BEGIN TRANSACTION")
    
    for tk in taikhoans:
        matk, tendangnhap, matkhau = tk
        username = tendangnhap if tendangnhap else matk
        
        # Kiểm tra xem user này đã có chưa
        cursor.execute("SELECT id FROM auth_user WHERE username = ?", (username,))
        row = cursor.fetchone()
        
        if row:
            user_id = row[0]
        else:
            # Insert trực tiếp với pass chưa hash (khách có thể ko login đc ngay nếu ko dùng mã hash pbkdf2, nhưng view Tích điểm sẽ chạy đc)
            # Khách có thể reset pass lại sau
            user_id = next_id
            cursor.execute("""
                INSERT INTO auth_user (id, password, is_superuser, username, last_name, email, is_staff, is_active, date_joined, first_name)
                VALUES (?, ?, 0, ?, '', '', 0, 1, ?, '')
            """, (user_id, matkhau, username, now))
            next_id += 1
            
        tk_to_user[matk] = user_id

    # Cập nhật accounts_khachhang
    cursor.execute("SELECT MaKH, MaTK_id FROM accounts_khachhang")
    for makh, matk_id in cursor.fetchall():
        if matk_id in tk_to_user:
            cursor.execute("UPDATE accounts_khachhang SET user_id = ? WHERE MaKH = ?", (tk_to_user[matk_id], makh))
            
    # Cập nhật accounts_nhanvien
    cursor.execute("SELECT MaNV, MaTK_id FROM accounts_nhanvien")
    for manv, matk_id in cursor.fetchall():
        if matk_id in tk_to_user:
            cursor.execute("UPDATE accounts_nhanvien SET user_id = ? WHERE MaNV = ?", (tk_to_user[matk_id], manv))

    cursor.execute("COMMIT")
    conn.close()
    print("Migration dữ liệu thành công!")

if __name__ == '__main__':
    run()
