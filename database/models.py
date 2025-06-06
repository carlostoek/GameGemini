from sqlalchemy import Column, Integer, String, BigInteger, DateTime, Boolean, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.ext.asyncio import AsyncAttrs

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

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', points={self.points}, level={self.level})>"

class Reward(AsyncAttrs, Base):
    __tablename__ = "rewards"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text)
    cost = Column(Integer, nullable=False)
    stock = Column(Integer, default=-1) # -1 for unlimited
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())

class Mission(AsyncAttrs, Base):
    __tablename__ = "missions"
    id = Column(String, primary_key=True) # Unique ID like 'daily_click_post'
    name = Column(String, nullable=False)
    description = Column(Text)
    points_reward = Column(Integer, nullable=False)
    type = Column(String, nullable=False) # 'daily', 'weekly', 'one_time', 'event'
    is_active = Column(Boolean, default=True)
    requires_action = Column(Boolean, default=False) # True if requires a specific button click/action outside the bot's menu
    action_data = Column(JSON, nullable=True) # e.g., {'button_id': 'unique_button_id'} or {'trivia_id': 1}
    created_at = Column(DateTime, default=func.now())

class Event(AsyncAttrs, Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    multiplier = Column(Integer, default=1) # e.g., 2 for double points
    is_active = Column(Boolean, default=False)
    start_time = Column(DateTime, default=func.now())
    end_time = Column(DateTime, nullable=True) # Nullable for indefinite events
    created_at = Column(DateTime, default=func.now())
