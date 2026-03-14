import logging
import os
from datetime import datetime, timedelta, timezone

import aiosqlite
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DB_PATH = "stats.db"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                username TEXT,
                first_name TEXT,
                timestamp INTEGER NOT NULL
            )
        """)
        await db.commit()


async def track_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.from_user:
        return

    user = msg.from_user
    timestamp = int(msg.date.timestamp())

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO messages (chat_id, user_id, username, first_name, timestamp) VALUES (?, ?, ?, ?, ?)",
            (msg.chat_id, user.id, user.username, user.first_name, timestamp),
        )
        await db.commit()


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    since = int((datetime.now(timezone.utc) - timedelta(hours=24)).timestamp())

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            SELECT first_name, username, COUNT(*) as cnt
            FROM messages
            WHERE chat_id = ? AND timestamp >= ?
            GROUP BY user_id
            ORDER BY cnt DESC
            """,
            (chat_id, since),
        )
        rows = await cursor.fetchall()

    if not rows:
        await update.message.reply_text("За последние 24 часа сообщений нет.")
        return

    lines = ["Статистика за последние 24 часа:\n"]
    for i, (first_name, username, cnt) in enumerate(rows, start=1):
        name = f"@{username}" if username else first_name
        lines.append(f"{i}. {name} — {cnt} сообщ.")

    await update.message.reply_text("\n".join(lines))


async def post_init(application):
    await init_db()


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, track_message))
    app.add_handler(CommandHandler("stats", stats))

    logger.info("Бот запущен")
    app.run_polling()


if __name__ == "__main__":
    main()
