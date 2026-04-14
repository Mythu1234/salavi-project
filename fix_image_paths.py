import sqlite3

# Kết nối database
db_path = 'd:/python/LTW/CSKH_04dl/db.sqlite3'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Danh sách cập nhật (Từ tên có dấu sang không dấu)
updates = [
    ('doitra_images/Áo.jpg', 'doitra_images/Ao.jpg'),
    ('doitra_images/ÁO_ĐEN.jpg', 'doitra_images/AO_DEN.jpg'),
    ('doitra_images/ÁO_KIỂU.jpg', 'doitra_images/AO_KIEU.jpg'),
    ('doitra_images/Bánh_mì.jpg', 'doitra_images/Banh_mi.jpg'),
    ('doitra_images/BODY_NỮ.jpg', 'doitra_images/BODY_NU.jpg'),
]

count = 0
for old_path, new_path in updates:
    cursor.execute("UPDATE orders_doitra SET HinhAnh = ? WHERE HinhAnh = ?", (new_path, old_path))
    if cursor.rowcount > 0:
        print(f"Updated: {old_path} -> {new_path}")
        count += 1

conn.commit()
conn.close()
print(f"Finished. Total updated: {count}")
