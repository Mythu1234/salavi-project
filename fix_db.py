import sqlite3
import copy

db_path = r'd:\python\LTW\CSKH_04dl\db.sqlite3'

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys=off;")
    cursor.execute("BEGIN TRANSACTION;")
    
    # Tạo bảng mới định nghĩa lại foreign key đúng chuẩn
    cursor.execute("""
    CREATE TABLE new_orders_doitra (
        "MaDoiTra" varchar(10) NOT NULL PRIMARY KEY, 
        "LoaiYeuCau" varchar(50) NOT NULL, 
        "NgayYeuCau" date NOT NULL, 
        "LyDo" varchar(200) NOT NULL, 
        "HinhAnh" varchar(100) NOT NULL, 
        "TrangThai" varchar(50) NOT NULL, 
        "GhiChuXuLy" varchar(100) NOT NULL, 
        "MaCTDH_id" bigint NOT NULL REFERENCES "orders_chitietdonhang" ("id") DEFERRABLE INITIALLY DEFERRED, 
        "MaKH_id" varchar(10) NOT NULL REFERENCES "accounts_khachhang" ("MaKH") DEFERRABLE INITIALLY DEFERRED, 
        "MaNV_id" varchar(10) NOT NULL REFERENCES "accounts_nhanvien" ("MaNV") DEFERRABLE INITIALLY DEFERRED
    )
    """)
    
    # Copy data qua
    cursor.execute("""
    INSERT INTO new_orders_doitra 
    SELECT MaDoiTra, LoaiYeuCau, NgayYeuCau, LyDo, HinhAnh, TrangThai, GhiChuXuLy, CAST(MaCTDH_id AS bigint), MaKH_id, MaNV_id 
    FROM orders_doitra;
    """)
    
    # Drop bảng cũ và rename bảng mới
    cursor.execute("DROP TABLE orders_doitra;")
    cursor.execute("ALTER TABLE new_orders_doitra RENAME TO orders_doitra;")
    
    cursor.execute("COMMIT;")
    cursor.execute("PRAGMA foreign_keys=on;")
    print("FIX DATABASE SUCCESS!")
except Exception as e:
    cursor.execute("ROLLBACK;")
    print("ERROR:", e)
finally:
    conn.close()
