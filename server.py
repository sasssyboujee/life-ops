import os
import sqlite3
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="Life Operations Engine API")

# Configure CORS so local React dev server (Vite) can query this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "life_ops.db")

class TransactionResponse(BaseModel):
    id: int
    timestamp: str
    merchant: str
    category: str
    amount_sgd: float
    notes: Optional[str] = ""
    has_image: bool

class WorkoutResponse(BaseModel):
    id: int
    timestamp: str
    exercise: str
    sets: int
    reps: int
    weight_kg: float
    rpe: int
    fatigue_flags: Optional[str] = ""
    has_image: bool

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/api/transactions", response_model=List[TransactionResponse])
def get_transactions():
    if not os.path.exists(DB_PATH):
        return []
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, timestamp, merchant, category, amount_sgd, notes, 
               (image_blob IS NOT NULL AND length(image_blob) > 0) AS has_image 
        FROM transactions 
        ORDER BY timestamp DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@app.get("/api/workouts", response_model=List[WorkoutResponse])
def get_workouts():
    if not os.path.exists(DB_PATH):
        return []
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, timestamp, exercise, sets, reps, weight_kg, rpe, fatigue_flags, 
               (image_blob IS NOT NULL AND length(image_blob) > 0) AS has_image 
        FROM workouts 
        ORDER BY timestamp DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@app.get("/api/transactions/{id}/image")
def get_transaction_image(id: int):
    if not os.path.exists(DB_PATH):
        raise HTTPException(status_code=404, detail="Database not found")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT image_blob FROM transactions WHERE id = ?", (id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row or not row["image_blob"]:
        raise HTTPException(status_code=404, detail="Image not found")
        
    return Response(content=row["image_blob"], media_type="image/jpeg")

@app.get("/api/workouts/{id}/image")
def get_workout_image(id: int):
    if not os.path.exists(DB_PATH):
        raise HTTPException(status_code=404, detail="Database not found")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT image_blob FROM workouts WHERE id = ?", (id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row or not row["image_blob"]:
        raise HTTPException(status_code=404, detail="Image not found")
        
    return Response(content=row["image_blob"], media_type="image/jpeg")

# Serve React frontend static build files if they exist
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dashboard", "dist")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
