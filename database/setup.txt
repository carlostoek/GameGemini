from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool # NullPool es adecuado para Railway, para SQLite local puedes mantenerlo o quitarlo
from database.models import Base
from config import Config

async def init_db():
    engine = create_async_engine(Config.DATABASE_URL, echo=False, poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    return engine

async def get_session():
    engine = await init_db() # Ensure db is initialized
    async_session = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    return async_session
