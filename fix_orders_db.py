import sqlite3

def run():
    conn = sqlite3.connect('db.sqlite3', isolation_level=None)
    cursor = conn.cursor()
    cursor.execute("BEGIN TRANSACTION")

    # Kiểm tra xem orders_chitietdonhang có cột id chưa
    cursor.execute("PRAGMA table_info(orders_chitietdonhang)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'id' not in columns:
        # Lấy dữ liệu cũ
        cursor.execute("SELECT MaCTDH, SoLuong, DonGia, ThanhTien, MaCTSP_id, MaDonHang_id FROM orders_chitietdonhang")
        rows = cursor.fetchall()

        # Xoá bảng cũ
        cursor.execute("DROP TABLE orders_chitietdonhang")

        # Tạo bảng mới với cấu trúc chuẩn
        cursor.execute("""
            CREATE TABLE "orders_chitietdonhang" (
                "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, 
                "SoLuong" integer NOT NULL, 
                "DonGia" decimal NOT NULL, 
                "ThanhTien" decimal NOT NULL, 
                "MaBTSP_id" varchar(10) NOT NULL REFERENCES "products_bienthesanpham" ("MaBTSP") DEFERRABLE INITIALLY DEFERRED, 
                "MaDonHang_id" varchar(10) NOT NULL REFERENCES "orders_donhang" ("MaDonHang") DEFERRABLE INITIALLY DEFERRED
            )
        """)

        # Insert dữ liệu đồng thời map ID
        old_ctdh_to_new_id = {}
        next_id = 1
        for row in rows:
            mactdh, soluong, dongia, thanhtien, mactsp_id, madonhang_id = row
            cursor.execute("""
                INSERT INTO orders_chitietdonhang (id, SoLuong, DonGia, ThanhTien, MaBTSP_id, MaDonHang_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (next_id, soluong, dongia, thanhtien, mactsp_id, madonhang_id))
            old_ctdh_to_new_id[mactdh] = next_id
            next_id += 1

        # Cập nhật orders_doitra để trỏ tới integer id thay vì string MaCTDH
        cursor.execute("SELECT MaDoiTra, MaCTDH_id FROM orders_doitra")
        doitras = cursor.fetchall()
        for madoitra, mactdh_id in doitras:
            if mactdh_id in old_ctdh_to_new_id:
                new_id = old_ctdh_to_new_id[mactdh_id]
                cursor.execute("UPDATE orders_doitra SET MaCTDH_id = ? WHERE MaDoiTra = ?", (new_id, madoitra))
            else:
                # Nếu không map được (có thể giá trị mactdh_id là integer rồi?)
                pass

    cursor.execute("COMMIT")
    conn.close()
    print("Done!")

if __name__ == '__main__':
    run()
