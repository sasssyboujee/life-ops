import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "life_ops.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        merchant TEXT,
        category TEXT,
        amount_sgd REAL,
        notes TEXT,
        image_blob BLOB
    )""")
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS workouts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        exercise TEXT,
        sets INTEGER,
        reps INTEGER,
        weight_kg REAL,
        rpe INTEGER,
        fatigue_flags TEXT,
        image_blob BLOB
    )""")
    
    # Run migrations for existing databases that don't have the column
    try:
        cursor.execute("ALTER TABLE transactions ADD COLUMN image_blob BLOB")
        print("[*] Added image_blob column to transactions table.")
    except sqlite3.OperationalError:
        pass  # Column already exists
        
    try:
        cursor.execute("ALTER TABLE workouts ADD COLUMN image_blob BLOB")
        print("[*] Added image_blob column to workouts table.")
    except sqlite3.OperationalError:
        pass  # Column already exists
        
    conn.commit()
    conn.close()
    print(f"[+] Database provisioned successfully at: {DB_PATH}")

if __name__ == "__main__":
    init_db()
