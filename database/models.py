# database/models.py
from sqlalchemy import Column, Integer, String, BigInteger, DateTime, Boolean, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.future import select

Base = declarative_base()

class User(AsyncAttrs, Base):
    __tablename__ = "users"
    id = Column(BigInteger, primary_key=True, unique=True) # Telegram User ID
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    points = Column(Integer, default=0)
    level = Column(Integer, default=1)
    achievements = Column(JSON, default={}) # {'achievement_id': timestamp_isoformat}
    missions_completed = Column(JSON, default={}) # {'mission_id': timestamp_isoformat}
    # Track last reset for daily/weekly missions
    last_daily_mission_reset = Column(DateTime, default=func.now())
    last_weekly_mission_reset = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # ¡NUEVA COLUMNA para el estado del menú!
    menu_state = Column(String, default="root") # e.g., "root", "profile", "missions", "rewards"

    # ¡NUEVA COLUMNA para registrar reacciones a mensajes del canal!
    # Guarda un diccionario donde la clave es el message_id del canal y el valor es un booleano (True)
    # o el timestamp de la reacción para futura expansión si necesitamos historial.
    # Por ahora, un simple booleano es suficiente para registrar si el usuario ya reaccionó a ese mensaje.
    channel_reactions = Column(JSON, default={}) # {'message_id': True}

class Reward(AsyncAttrs, Base):
    __tablename__ = "rewards"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text)
    cost = Column(Integer, default=0)
    stock = Column(Integer, default=-1) # -1 for unlimited
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())

class Mission(AsyncAttrs, Base):
    __tablename__ = "missions"
    id = Column(String, primary_key=True, unique=True) # e.g., 'daily_login', 'event_trivia_challenge'
    name = Column(String, nullable=False)
    description = Column(Text)
    points_reward = Column(Integer, default=0)
    type = Column(String, default="one_time") # 'daily', 'weekly', 'one_time', 'event', 'reaction'
    is_active = Column(Boolean, default=True)
    requires_action = Column(Boolean, default=False) # True if requires a specific button click/action outside the bot's menu
    # action_data puede ser usado para especificar, por ejemplo, qué 'button_id' de reacción completa la misión
    action_data = Column(JSON, nullable=True) # e.g., {'button_id': 'like_post_1'} or {'target_message_id': 12345}
    created_at = Column(DateTime, default=func.now())

class Event(AsyncAttrs, Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    multiplier = Column(Integer, default=1) # e.g., 2 for double points
    is_active = Column(Boolean, default=True)
    start_time = Column(DateTime, default=func.now())
    end_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())


# Funciones para manejar el estado del menú del usuario
async def get_user_menu_state(session, user_id: int) -> str:
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user and user.menu_state:
        return user.menu_state
    return "root"

async def set_user_menu_state(session, user_id: int, state: str):
    user = await session.get(User, user_id)
    if user:
        user.menu_state = state
        await session.commit()
        await session.refresh(user)

