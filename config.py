import os

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    ADMIN_ID = int(os.getenv("ADMIN_ID"))
    CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

    # URL de la base de datos
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///gamification.db")
