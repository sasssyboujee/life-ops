import os
from dotenv import load_dotenv

# Load env variables before other imports to ensure they're available
load_dotenv()

import asyncio
import sqlite3
from PIL import Image
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
        # Columns: 0:id, 1:timestamp, 2:merchant, 3:category, 4:amount_sgd, 5:notes, 6:image_blob
        if row and row[2] == "Fairprice" and row[4] == 15.50:
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
        # Columns: 0:id, 1:timestamp, 2:exercise, 3:sets, 4:reps, 5:weight_kg, 6:rpe, 7:fatigue_flags, 8:image_blob
        if row and row[2] == "Squats" and row[5] == 120.0:
            print("✅ Athletic pipeline test PASSED")
        else:
            print("❌ Athletic pipeline test FAILED (check database values)")
    except Exception as e:
        print(f"❌ Athletic pipeline test FAILED with exception: {e}")

async def test_image_pipeline():
    print("\n--- 3. Testing Image Pipeline ---")
    dummy_img = "test_verify_image.jpg"
    # Generate a mock receipt image with readable text using Pillow to satisfy multimodal LLM
    from PIL import ImageDraw
    img = Image.new('RGB', (400, 200), color='white')
    draw = ImageDraw.Draw(img)
    # Simple block text to simulate a receipt
    draw.text((20, 30), "Fairprice Groceries", fill='black')
    draw.text((20, 60), "1 x Apples - 5.50 SGD", fill='black')
    draw.text((20, 90), "1 x Milk - 10.00 SGD", fill='black')
    draw.text((20, 120), "Total: 15.50 SGD", fill='black')
    draw.text((20, 150), "Thank you for shopping!", fill='black')
    img.save(dummy_img, 'JPEG')
        
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
