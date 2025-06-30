from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import os
import sqlite3
import openai
import asyncio
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return '✅ Bot is live and working on Render!'

# Rest of your bot logic... (handlers, webhook setup, etc)


BOT_TOKEN = os.environ.get("BOT_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect("notes.db")
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            user_id INTEGER,
            note TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome! Type anything to chat with AI. Use /save <text> to save a note. Use /notes to view them.")

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": user_input}]
    )
    reply = response["choices"][0]["message"]["content"]
    await update.message.reply_text(reply)

async def save_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    note = " ".join(context.args)
    if not note:
        await update.message.reply_text("Please provide a note to save.")
        return
    conn = sqlite3.connect("notes.db")
    cur = conn.cursor()
    cur.execute("INSERT INTO notes (user_id, note) VALUES (?, ?)", (user_id, note))
    conn.commit()
    conn.close()
    await update.message.reply_text("Note saved!")

async def get_notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    conn = sqlite3.connect("notes.db")
    cur = conn.cursor()
    cur.execute("SELECT note FROM notes WHERE user_id = ?", (user_id,))
    rows = cur.fetchall()
    conn.close()
    if not rows:
        await update.message.reply_text("You have no saved notes.")
    else:
        notes = "\n- ".join([row[0] for row in rows])
        await update.message.reply_text(f"Your notes:\n- {notes}")

application = Application.builder().token(BOT_TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("save", save_note))
application.add_handler(CommandHandler("notes", get_notes))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

@app.post("/")
def webhook():
    update = Update.de_json(request.get_json(force=True), Bot(BOT_TOKEN))
    asyncio.run(application.process_update(update))
    return "ok"

if __name__ == "__main__":
    app.run(port=8000)
