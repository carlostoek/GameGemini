import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    ADMIN_ID = int(os.getenv("ADMIN_ID"))
    # Usando SQLite para pruebas locales. El archivo se creará como gamification.db
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///gamification.db")
    CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
gamification.d