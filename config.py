# config.py

import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN", "TU_TOKEN_AQUI")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///gamegemini.db")
    ADMINS = [int(admin_id) for admin_id in os.getenv("ADMINS", "").split(",") if admin_id]

# Motor de base de datos y sesión asíncrona
engine = create_async_engine(Config.DATABASE_URL, echo=False)
session_maker = async_sessionmaker(bind=engine, expire_on_commit=False)
