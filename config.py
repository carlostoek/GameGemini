from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from database.models import Base

DATABASE_URL = "sqlite+aiosqlite:///gamegemini.db"  # O ajusta a tu motor real

engine = create_async_engine(DATABASE_URL, echo=False)
session_maker = async_sessionmaker(bind=engine, expire_on_commit=False)
