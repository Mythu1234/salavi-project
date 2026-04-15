import sqlite3
import json

def get_data():
    conn = sqlite3.connect("db.sqlite3")
    cursor = conn.cursor()
    
    print("--- orders_chitietdonhang ---")
    cursor.execute("SELECT id FROM orders_chitietdonhang")
    print("IDs:", [r[0] for r in cursor.fetchall()])
    
    print("\n--- orders_doitra ---")
    cursor.execute("SELECT MaDoiTra, MaCTDH_id FROM orders_doitra")
    for row in cursor.fetchall():
        print(f"MaDoiTra: {row[0]}, MaCTDH_id: {row[1]}")
    
    conn.close()

if __name__ == "__main__":
    get_data()
