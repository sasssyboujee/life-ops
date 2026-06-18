import os
import re
import sqlite3
import contextvars
import ollama
from google.antigravity import Agent, LocalAgentConfig
from google.antigravity.hooks import policy

# Global thread-safe context variable to hold the binary data of the image currently being processed
current_image_blob = contextvars.ContextVar("current_image_blob", default=None)


DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "life_ops.db")

# ==========================================
# 1. Custom Tools
# ==========================================
def log_expense(merchant: str, category: str, amount_sgd: float, notes: str) -> str:
    """Inserts a validated financial record into the SQLite database.

    Args:
        merchant: The place or person where the money was spent.
        category: Must be Groceries, Dining Out, Travel, Gear, or Other.
        amount_sgd: The amount of money spent in Singapore Dollars (SGD).
        notes: Context or details about the expense.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    img_blob = current_image_blob.get()
    cursor.execute(
        "INSERT INTO transactions (merchant, category, amount_sgd, notes, image_blob) VALUES (?, ?, ?, ?, ?)",
        (merchant, category, amount_sgd, notes, img_blob)
    )
    conn.commit()
    conn.close()
    return f"Successfully logged expense: {amount_sgd} SGD at {merchant} ({category})."

def log_workout(exercise: str, sets: int, reps: int, weight_kg: float, rpe: int, fatigue_flags: list[str]) -> str:
    """Inserts a validated athletic performance record into the SQLite database.

    Args:
        exercise: Name of the exercise, e.g. "Squats", "Bench Press".
        sets: Number of sets performed.
        reps: Number of repetitions per set.
        weight_kg: Weight lifted in kilograms.
        rpe: Rate of Perceived Exertion (1 to 10 scale).
        fatigue_flags: List of symptoms or recovery notes, e.g. ["stiff", "knee pain"].
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    flags = ",".join(fatigue_flags) if fatigue_flags else ""
    img_blob = current_image_blob.get()
    cursor.execute(
        "INSERT INTO workouts (exercise, sets, reps, weight_kg, rpe, fatigue_flags, image_blob) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (exercise, sets, reps, weight_kg, rpe, flags, img_blob)
    )
    conn.commit()
    conn.close()
    return f"Successfully logged workout: {sets}x{reps} {exercise} at {weight_kg} kg."

# ==========================================
# 2. Resilient Routing Heuristics
# ==========================================
def local_heuristic_route(text: str) -> str:
    """Falls back to simple regex matching when Ollama is unavailable."""
    text_lower = text.lower()
    
    financial_keywords = ["sgd", "spent", "buy", "bought", "groceries", "price", "cost", "dining", "gear", "expense"]
    athletic_keywords = ["squats", "bench", "sets", "reps", "kg", "workout", "gym", "rpe", "fatigue", "knee", "stiff", "lifted", "conditioning"]
    
    fin_score = sum(1 for kw in financial_keywords if kw in text_lower)
    ath_score = sum(1 for kw in athletic_keywords if kw in text_lower)
    
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
            model='llama3.2',
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

    # If local classification is completely unknown, try heuristics
    if intent not in ["FINANCIAL", "ATHLETIC"]:
        # Standard default logic if heuristic returns UNKNOWN
        intent = "FINANCIAL" if "sgd" in raw_input.lower() or "spent" in raw_input.lower() else "ATHLETIC"

    # 2. Sandbox Security Policies
    # Blocks all default tools (view_file, edit_file, run_command) and allows only logging tools
    secure_policies = [
        policy.deny_all(),
        policy.allow("log_expense"),
        policy.allow("log_workout")
    ]

    # 3. Cloud Agent Execution
    if intent == "FINANCIAL":
        config = LocalAgentConfig(
            system_instructions=(
                "You are an exact financial auditor. Extract the transaction details "
                "from the prompt and execute the log_expense tool. Categorize strictly "
                "as Groceries, Dining Out, Travel, Gear, or Other. Do not output anything "
                "other than the direct result confirmation."
            ),
            tools=[log_expense],
            policies=secure_policies
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
            policies=secure_policies
        )
        async with Agent(config) as agent:
            response = await agent.chat(raw_input)
            return await response.text()
            
    return "Error: System could not classify input intent."

async def process_image(image_path: str) -> str:
    """Processes an image (receipt or workout log) using a multimodal Antigravity Agent."""
    from google.antigravity import Agent, LocalAgentConfig
    from google.antigravity.types import Image
    from google.antigravity.hooks import policy

    # Define secure policies allowing only logging tools
    secure_policies = [
        policy.deny_all(),
        policy.allow("log_expense"),
        policy.allow("log_workout")
    ]
    
    # Read the raw image bytes in binary mode
    with open(image_path, "rb") as f:
        img_bytes = f.read()
        
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
            policies=secure_policies
        )
        
        async with Agent(config) as agent:
            response = await agent.chat(["Please analyze this image and log the entry using the correct tool.", image])
            return await response.text()
    finally:
        current_image_blob.reset(token)

