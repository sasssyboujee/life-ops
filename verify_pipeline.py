import os
from dotenv import load_dotenv

# Load env variables before other imports to ensure they're available
load_dotenv()

import asyncio
import sqlite3
from ai_engine import process_input, process_image

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "life_ops.db")

async def test_financial_intent():
    print("\n--- 1. Testing Financial Intent ---")
    test_input = "Spent 15.50 SGD on groceries at Fairprice"
    print(f"Input: '{test_input}'")
    try:
        res = await process_input(test_input)
        print(f"Response: {res}")
        
        # Verify db insert
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM transactions ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        print(f"Latest DB Row: {row}")
        if row and "Fairprice" in row[1] and row[3] == 15.50:
            print("✅ Financial pipeline test PASSED")
        else:
            print("❌ Financial pipeline test FAILED (check database values)")
    except Exception as e:
        print(f"❌ Financial pipeline test FAILED with exception: {e}")

async def test_athletic_intent():
    print("\n--- 2. Testing Athletic Intent ---")
    test_input = "Squats 120kg 3x5, RPE 8. feeling stiff in knee."
    print(f"Input: '{test_input}'")
    try:
        res = await process_input(test_input)
        print(f"Response: {res}")
        
        # Verify db insert
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM workouts ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        print(f"Latest DB Row: {row}")
        if row and "Squats" in row[1] and row[4] == 120.0:
            print("✅ Athletic pipeline test PASSED")
        else:
            print("❌ Athletic pipeline test FAILED (check database values)")
    except Exception as e:
        print(f"❌ Athletic pipeline test FAILED with exception: {e}")

async def test_image_pipeline():
    print("\n--- 3. Testing Image Pipeline ---")
    dummy_img = "test_verify_image.jpg"
    with open(dummy_img, "wb") as f:
        # Standard JPG header bytes to satisfy parser
        f.write(b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00\x60\x00\x60\x00\x00\xFF\xDB\x00\x43\x00")
        f.write(b"\x00" * 100) # dummy padding
        
    print(f"Created dummy image: {dummy_img}")
    try:
        print("Calling process_image (this expects valid Antigravity Agent runtime)...")
        res = await process_image(dummy_img)
        print(f"Response: {res}")
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, length(image_blob) FROM transactions WHERE image_blob IS NOT NULL ORDER BY id DESC LIMIT 1")
        fin_row = cursor.fetchone()
        
        cursor.execute("SELECT id, length(image_blob) FROM workouts WHERE image_blob IS NOT NULL ORDER BY id DESC LIMIT 1")
        gym_row = cursor.fetchone()
        
        conn.close()
        
        print(f"Latest Transaction with Blob: {fin_row}")
        print(f"Latest Workout with Blob: {gym_row}")
        
        if fin_row or gym_row:
            print("✅ Image pipeline BLOB storage test PASSED")
        else:
            print("❌ Image pipeline BLOB storage test FAILED (no BLOB found in DB)")
    except Exception as e:
        print(f"❌ Image pipeline test FAILED with exception: {e}")
    finally:
        if os.path.exists(dummy_img):
            os.remove(dummy_img)

async def main():
    if not os.path.exists(DB_PATH):
        print("[!] Database not found. Running db_init.py first...")
        os.system(".venv/bin/python db_init.py")
        
    await test_financial_intent()
    await test_athletic_intent()
    await test_image_pipeline()

if __name__ == "__main__":
    asyncio.run(main())
