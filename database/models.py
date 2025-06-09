from sqlalchemy import Column, Integer, String, BigInteger, DateTime, Boolean, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.ext.asyncio import AsyncAttrs

Base = declarative_base()

class User(AsyncAttrs, Base):
    __tablename__ = "users"
    id = Column(BigInteger, primary_key=True, unique=True)  # Telegram User ID
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    points = Column(Integer, default=0)
    level = Column(Integer, default=1)
    achievements = Column(JSON, default={})  # {'achievement_id': timestamp_isoformat}
    missions_completed = Column(JSON, default={})  # {'mission_id': timestamp_isoformat}
    last_daily_mission_reset = Column(DateTime, default=func.now())
    last_weekly_mission_reset = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    channel_reactions = Column(JSON, default={})  # {'message_id': True}

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', points={self.points}, level={self.level})>"

class Reward(AsyncAttrs, Base):
    __tablename__ = "rewards"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text)
    cost = Column(Integer, nullable=False)
    stock = Column(Integer, default=-1)  # -1 for unlimited

    def __repr__(self):
        return f"<Reward(id={self.id}, name='{self.name}', cost={self.cost}, stock={self.stock})>"

class Event(AsyncAttrs, Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=False)

    def __repr__(self):
        return f"<Event(id={self.id}, name='{self.name}', active={self.is_active})>"
