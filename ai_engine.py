import os
import re
import sqlite3
import contextvars
import asyncio
from contextlib import contextmanager
import ollama
from google.antigravity import Agent, LocalAgentConfig
from google.antigravity.types import Image
from google.antigravity.hooks import policy

# Global thread-safe context variable to hold the binary data of the image currently being processed
current_image_blob = contextvars.ContextVar("current_image_blob", default=None)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "life_ops.db")

# Compiled regex patterns with word boundaries (\b) for robust intent classification
FINANCIAL_REGEX = re.compile(r'\b(sgd|spent|buy|bought|groceries|price|cost|dining|gear|expense)\b', re.IGNORECASE)
ATHLETIC_REGEX = re.compile(r'\b(squats|bench|sets|reps|kg|workout|gym|rpe|fatigue|knee|stiff|lifted|conditioning)\b', re.IGNORECASE)

OLLAMA_MODEL = 'llama3.2'

# Reusable global sandbox security policy configuration
SECURE_POLICIES = [
    policy.deny_all(),
    policy.allow("log_expense"),
    policy.allow("log_workout")
]

@contextmanager
def get_db():
    """Context manager for safe SQLite transactions. Auto-commits and closes connection."""
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn.cursor()
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        print(f"[!] Database transaction failed: {e}")
        raise
    finally:
        conn.close()

# ==========================================
# 1. Custom Tools
# ==========================================
def log_expense(merchant: str, category: str, amount_sgd: float, notes: str) -> str:
    """Inserts a validated financial record into the SQLite database."""
    img_blob = current_image_blob.get()
    try:
        with get_db() as cursor:
            cursor.execute(
                "INSERT INTO transactions (merchant, category, amount_sgd, notes, image_blob) VALUES (?, ?, ?, ?, ?)",
                (merchant, category, amount_sgd, notes, img_blob)
            )
        return f"Successfully logged expense: {amount_sgd} SGD at {merchant} ({category})."
    except sqlite3.Error as e:
        return f"Database error logging expense: {e}"

def log_workout(exercise: str, sets: int, reps: int, weight_kg: float, rpe: int, fatigue_flags: list[str]) -> str:
    """Inserts a validated athletic performance record into the SQLite database."""
    flags = ",".join(fatigue_flags) if fatigue_flags else ""
    img_blob = current_image_blob.get()
    try:
        with get_db() as cursor:
            cursor.execute(
                "INSERT INTO workouts (exercise, sets, reps, weight_kg, rpe, fatigue_flags, image_blob) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (exercise, sets, reps, weight_kg, rpe, flags, img_blob)
            )
        return f"Successfully logged workout: {sets}x{reps} {exercise} at {weight_kg} kg."
    except sqlite3.Error as e:
        return f"Database error logging workout: {e}"

# ==========================================
# 2. Resilient Routing Heuristics
# ==========================================
def local_heuristic_route(text: str) -> str:
    """Falls back to simple regex matching when Ollama is unavailable."""
    fin_score = len(FINANCIAL_REGEX.findall(text))
    ath_score = len(ATHLETIC_REGEX.findall(text))
    
    if fin_score > ath_score and fin_score > 0:
        return "FINANCIAL"
    elif ath_score > fin_score and ath_score > 0:
        return "ATHLETIC"
    return "UNKNOWN"

# ==========================================
# 3. Execution Pipeline
# ==========================================
async def process_input(raw_input: str) -> str:
    # 1. Edge Classification (Ollama Llama3.2 with Local Regex Fallback)
    intent = "UNKNOWN"
    try:
        route_response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[{
                'role': 'user', 
                'content': f"Classify this text as either 'FINANCIAL' or 'ATHLETIC'. Reply with only one word. Text: {raw_input}"
            }]
        )
        intent = route_response['message']['content'].strip().upper()
    except Exception as e:
        print(f"[!] Ollama connection failed ({e}). Falling back to local heuristics...")
        intent = local_heuristic_route(raw_input)
        
    print(f"[*] Classified intent: {intent}")

    # If local classification is completely unknown, try heuristics fallback
    if intent not in ["FINANCIAL", "ATHLETIC"]:
        intent = "FINANCIAL" if "sgd" in raw_input.lower() or "spent" in raw_input.lower() else "ATHLETIC"

    # 2. Cloud Agent Execution
    if intent == "FINANCIAL":
        config = LocalAgentConfig(
            system_instructions=(
                "You are an exact financial auditor. Extract the transaction details "
                "from the prompt and execute the log_expense tool. Categorize strictly "
                "as Groceries, Dining Out, Travel, Gear, or Other. Do not output anything "
                "other than the direct result confirmation."
            ),
            tools=[log_expense],
            policies=SECURE_POLICIES
        )
        async with Agent(config) as agent:
            response = await agent.chat(raw_input)
            return await response.text()
            
    elif intent == "ATHLETIC":
        config = LocalAgentConfig(
            system_instructions=(
                "You are a varsity sports scientist. Extract the training volume and metrics "
                "from the prompt and execute the log_workout tool. Track any mentioned "
                "stiffness, joint pain, or recovery notes in the fatigue_flags array. "
                "Do not output anything other than the direct result confirmation."
            ),
            tools=[log_workout],
            policies=SECURE_POLICIES
        )
        async with Agent(config) as agent:
            response = await agent.chat(raw_input)
            return await response.text()
            
    return "Error: System could not classify input intent."

async def process_image(image_path: str) -> str:
    """Processes an image (receipt or workout log) using a multimodal Antigravity Agent."""
    
    # Read the raw image bytes asynchronously to avoid blocking the event loop
    def _read_file():
        with open(image_path, "rb") as f:
            return f.read()
            
    img_bytes = await asyncio.to_thread(_read_file)
        
    # Set the ContextVar so tool invocations in this task context can read the binary data
    token = current_image_blob.set(img_bytes)
    
    try:
        # Load image using SDK's Image class
        image = Image.from_file(image_path)
        
        # Configure a multimodal agent that can use both tools
        config = LocalAgentConfig(
            system_instructions=(
                "You are a helpful personal tracking assistant. Analyze the image provided (which could be a receipt, invoice, "
                "workout log, or whiteboard photo) and log the details using the appropriate tool:\n"
                "- If it is a receipt or financial transaction, extract the merchant, category (Groceries, Dining Out, Travel, Gear, or Other), "
                "amount in SGD, and any notes, then call the log_expense tool.\n"
                "- If it is a gym workout log, whiteboard, or exercise record, extract the exercise, sets, reps, weight in kg, RPE, "
                "and fatigue flags, then call the log_workout tool.\n"
                "Only output the tool call result confirmation."
            ),
            tools=[log_expense, log_workout],
            policies=SECURE_POLICIES
        )
        
        async with Agent(config) as agent:
            response = await agent.chat(["Please analyze this image and log the entry using the correct tool.", image])
            return await response.text()
    finally:
        current_image_blob.reset(token)

