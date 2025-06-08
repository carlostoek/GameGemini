# database/models.py
from sqlalchemy import Column, Integer, String, BigInteger, DateTime, Boolean, JSON, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import relationship

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
    last_daily_mission_reset = Column(DateTime, default=func.now())
    last_weekly_mission_reset = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    channel_reactions = Column(JSON, default={}) # {'message_id': True, 'message_id_2': True}

    # NUEVOS CAMPOS para gamificación y administración
    is_admin = Column(Boolean, default=False)
    referred_by = Column(BigInteger, nullable=True) # Telegram ID del referido (si aplica)
    last_point_date = Column(DateTime, nullable=True)
    weekly_streak = Column(Integer, default=0)
    monthly_streak = Column(Integer, default=0)

    # Relaciones
    point_logs = relationship("PointLog", back_populates="user")
    achievements_rel = relationship("Achievement", back_populates="user")

class PointLog(Base):
    __tablename__ = "point_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"))
    points = Column(Integer)
    action_type = Column(String) # 'interaction', 'purchase', 'mission', etc.
    description = Column(String, nullable=True)
    timestamp = Column(DateTime, default=func.now())

    user = relationship("User", back_populates="point_logs")

class Achievement(Base):
    __tablename__ = "achievements"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"))
    name = Column(String)
    unlocked_at = Column(DateTime, default=func.now())

    user = relationship("User", back_populates="achievements_rel")

# Modelos base para compatibilidad (puedes expandirlos según tu lógica)
class Mission(Base):
    __tablename__ = "missions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    description = Column(String)
    type = Column(String)  # 'diaria', 'semanal', 'colaborativa', etc.
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

class Reward(Base):
    __tablename__ = "rewards"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    description = Column(String)
    cost_in_points = Column(Integer)
    is_active = Column(Boolean, default=True)

class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    description = Column(String)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    is_active = Column(Boolean, default=True)
