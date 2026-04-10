import sqlite3

def run():
    conn = sqlite3.connect('db.sqlite3', isolation_level=None)
    cursor = conn.cursor()
    cursor.execute("BEGIN TRANSACTION")

    cursor.execute("SELECT MaDoiTra, LoaiYeuCau, NgayYeuCau, LyDo, HinhAnh, TrangThai, GhiChuXuLy, MaCTDH_id, MaKH_id, MaNV_id FROM orders_doitra")
    rows = cursor.fetchall()
    
    cursor.execute("DROP TABLE orders_doitra")
    
    cursor.execute("""
        CREATE TABLE "orders_doitra" (
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
    
    for row in rows:
        cursor.execute("INSERT INTO orders_doitra (MaDoiTra, LoaiYeuCau, NgayYeuCau, LyDo, HinhAnh, TrangThai, GhiChuXuLy, MaCTDH_id, MaKH_id, MaNV_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", row)

    cursor.execute("COMMIT")
    conn.close()
    print("Fixed orders_doitra database table successfully.")

if __name__ == '__main__':
    run()
