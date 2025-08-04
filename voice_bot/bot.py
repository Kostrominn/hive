import os
import random
import logging
from datetime import datetime
import sqlite3

import aiohttp
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VoiceBot:
    def __init__(self, telegram_token: str, upload_url: str):
        self.telegram_token = telegram_token
        self.upload_url = upload_url

        self.conn = sqlite3.connect('voice_metadata.db', check_same_thread=False)
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS voice_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                message_id INTEGER NOT NULL,
                file_name TEXT NOT NULL,
                remote_id TEXT NOT NULL,
                file_size INTEGER,
                duration INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
        )
        self.conn.commit()

        self.responses = [
            "Привет! Я записал голосовое сообщение, спасибо 🎵",
            "Привет, я гигачат 💪",
        ]

    async def upload_voice(self, data: bytes, file_name: str) -> str:
        """Upload voice bytes to remote server and return file identifier."""
        async with aiohttp.ClientSession() as session:
            form = aiohttp.FormData()
            form.add_field('file', data, filename=file_name, content_type='audio/ogg')
            async with session.post(self.upload_url, data=form) as resp:
                resp.raise_for_status()
                result = await resp.json()
                return result.get('file_id', '')

    async def handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            user_id = update.effective_user.id
            message_id = update.message.message_id
            voice = update.message.voice

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"voice_{user_id}_{timestamp}.ogg"

            voice_file = await voice.get_file()
            voice_bytes = await voice_file.download_as_bytearray()

            remote_id = await self.upload_voice(voice_bytes, file_name)

            self.conn.execute(
                """
                INSERT INTO voice_messages
                (user_id, message_id, file_name, remote_id, file_size, duration)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (user_id, message_id, file_name, remote_id, voice.file_size, voice.duration),
            )
            self.conn.commit()

            await update.message.reply_text(random.choice(self.responses))
            logger.info(f"Saved voice from {user_id} as {remote_id}")
        except Exception as e:
            logger.error(f"Error processing voice: {e}")
            await update.message.reply_text(
                "Произошла ошибка при обработке голосового сообщения"
            )

    def run(self):
        app = Application.builder().token(self.telegram_token).build()
        app.add_handler(MessageHandler(filters.VOICE, self.handle_voice))
        app.run_polling()


if __name__ == "__main__":
    TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
    UPLOAD_URL = os.environ.get("VOICE_UPLOAD_URL", "https://example.com/upload")

    bot = VoiceBot(TELEGRAM_TOKEN, UPLOAD_URL)
    bot.run()

