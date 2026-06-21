import os
import asyncio
import logging
from dotenv import load_dotenv

# Enable standard library logging to capture harness stderr traces
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Load env variables before other imports to ensure they're available
load_dotenv()

from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from ai_engine import process_input, process_image

# Load keys
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    print(f"[*] Received text: {user_text}")
    
    # Process through the AI pipeline
    result = await process_input(user_text)
    await update.message.reply_text(result)

async def handle_photo_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    print(f"[*] Received photo (dimensions: {photo.width}x{photo.height})")
    
    await update.message.reply_text("📸 Processing image...")
    
    local_path = None
    try:
        # Download file
        photo_file = await context.bot.get_file(photo.file_id)
        local_path = f"temp_photo_{photo.file_id}.jpg"
        await photo_file.download_to_drive(local_path)
        
        # Process image through the core Antigravity execution pipeline
        result = await process_image(local_path)
        await update.message.reply_text(result)
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error processing image: {e}")
    finally:
        # Clean up local file immediately
        if local_path and os.path.exists(local_path):
            os.remove(local_path)
            print(f"[*] 🗑️ Temporary photo deleted.")

def main():
    if not TELEGRAM_TOKEN:
        print("[!] ERROR: TELEGRAM_TOKEN environment variable is not set.")
        return
    if not GEMINI_API_KEY:
        print("[!] ERROR: GEMINI_API_KEY environment variable is not set.")
        return
        
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Text messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    
    # Photo messages
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo_message))
    
    print("[+] Telegram Listener active (Text + Photo enabled).")
    app.run_polling()

if __name__ == "__main__":
    main()
