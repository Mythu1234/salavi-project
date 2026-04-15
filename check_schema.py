import sqlite3
conn = sqlite3.connect("db.sqlite3")
cursor = conn.cursor()
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name IN ('orders_doitra', 'orders_chitietdonhang')")
for row in cursor.fetchall():
    print(row[0])
conn.close()
