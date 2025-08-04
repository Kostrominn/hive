import os
import random
import logging
from datetime import datetime
from pathlib import Path
import sqlite3

from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.service_account import Credentials

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VoiceBot:
    def __init__(self, telegram_token: str, credentials_path: str, drive_folder_id: str):
        self.telegram_token = telegram_token
        self.drive_folder_id = drive_folder_id

        credentials = Credentials.from_service_account_file(
            credentials_path,
            scopes=['https://www.googleapis.com/auth/drive.file']
        )
        self.drive_service = build('drive', 'v3', credentials=credentials)

        self.conn = sqlite3.connect('voice_metadata.db', check_same_thread=False)
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS voice_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                message_id INTEGER NOT NULL,
                file_name TEXT NOT NULL,
                google_drive_id TEXT NOT NULL,
                file_size INTEGER,
                duration INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        self.conn.commit()

        self.temp_dir = Path('temp_voices')
        self.temp_dir.mkdir(exist_ok=True)

        self.responses = [
            "Привет! Я записал голосовое сообщение, спасибо 🎵",
            "Привет, я гигачат 💪",
        ]

    async def handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            user_id = update.effective_user.id
            message_id = update.message.message_id
            voice = update.message.voice

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"voice_{user_id}_{timestamp}.ogg"
            temp_path = self.temp_dir / file_name

            voice_file = await voice.get_file()
            await voice_file.download_to_drive(temp_path)

            media = MediaFileUpload(str(temp_path), resumable=True)
            metadata = {'name': file_name, 'parents': [self.drive_folder_id]}
            uploaded = (
                self.drive_service.files()
                .create(body=metadata, media_body=media, fields='id')
                .execute()
            )
            drive_id = uploaded.get('id')

            self.conn.execute(
                """
                INSERT INTO voice_messages
                (user_id, message_id, file_name, google_drive_id, file_size, duration)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (user_id, message_id, file_name, drive_id, voice.file_size, voice.duration),
            )
            self.conn.commit()

            temp_path.unlink()

            await update.message.reply_text(random.choice(self.responses))
            logger.info(f"Saved voice {file_name} to Google Drive with id {drive_id}")
        except Exception as e:
            logger.error(f"Error processing voice: {e}")
            await update.message.reply_text("Произошла ошибка при обработке голосового сообщения")

    def run(self):
        app = Application.builder().token(self.telegram_token).build()
        app.add_handler(MessageHandler(filters.VOICE, self.handle_voice))
        app.run_polling()


if __name__ == "__main__":
    TELEGRAM_TOKEN = "7616618164:AAHCwDaOxaMQ-xc0tYEP9ufP0CnCO70sJPM"
    GOOGLE_CREDENTIALS = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "service_account.json")
    DRIVE_FOLDER_ID = os.environ.get("GOOGLE_DRIVE_FOLDER_ID", "root")

    bot = VoiceBot(TELEGRAM_TOKEN, GOOGLE_CREDENTIALS, DRIVE_FOLDER_ID)
    bot.run()
