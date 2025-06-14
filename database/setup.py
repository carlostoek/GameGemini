# database/setup.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool # NullPool es adecuado para Railway, para SQLite local puedes mantenerlo o quitarlo
from database.models import Base
from config import Config

# Hacemos que el motor sea una variable global o pasada, no creada repetidamente
_engine = None # Variable para almacenar el motor una vez inicializado

async def init_db():
    global _engine
    if _engine is None: # Solo crear el motor si no existe
        _engine = create_async_engine(Config.DATABASE_URL, echo=False, poolclass=NullPool)
        async with _engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    return _engine

async def get_session() -> async_sessionmaker[AsyncSession]:
    # get_session ya no llamará a init_db directamente
    # Asume que init_db ya fue llamado en el inicio de la app y _engine está disponible
    if _engine is None:
        raise RuntimeError("Database engine not initialized. Call init_db() first.")
    async_session = async_sessionmaker(bind=_engine, class_=AsyncSession, expire_on_commit=False)
    return async_session
