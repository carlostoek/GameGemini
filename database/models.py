from sqlalchemy import Column, Integer, String, BigInteger, DateTime, Boolean, JSON, Text from sqlalchemy.ext.declarative import declarative_base from sqlalchemy.sql import func from sqlalchemy.ext.asyncio import AsyncAttrs from sqlalchemy.future import select

Base = declarative_base()

class User(AsyncAttrs, Base): tablename = "users" id = Column(BigInteger, primary_key=True, unique=True)  # Telegram User ID username = Column(String, nullable=True) first_name = Column(String, nullable=True) last_name = Column(String, nullable=True) points = Column(Integer, default=0) level = Column(Integer, default=1) achievements = Column(JSON, default={})  # {'achievement_id': timestamp_isoformat} missions_completed = Column(JSON, default={})  # {'mission_id': timestamp_isoformat} last_daily_mission_reset = Column(DateTime, default=func.now()) menu_state = Column(String, default="root")  # Estado actual del menú del usuario

class Event(AsyncAttrs, Base): tablename = "events" id = Column(Integer, primary_key=True, autoincrement=True) name = Column(String, nullable=False) description = Column(Text) multiplier = Column(Integer, default=1)  # e.g., 2 for double points is_active = Column(Boolean, default=True) start_time = Column(DateTime, default=func.now()) end_time = Column(DateTime, nullable=True) created_at = Column(DateTime, default=func.now())

Funciones para manejar el estado del menú del usuario

async def get_user_menu_state(session, user_id: int) -> str: result = await session.execute(select(User).where(User.id == user_id)) user = result.scalar_one_or_none() if user and user.menu_state: return user.menu_state return "root"

async def set_user_menu_state(session, user_id: int, menu_name: str): result = await session.execute(select(User).where(User.id == user_id)) user = result.scalar_one_or_none() if user: user.menu_state = menu_name await session.commit()

