# database/models.py

from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, ForeignKey, func
)
from sqlalchemy.orm import declarative_base, relationship
import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(String, unique=True, index=True)
    username = Column(String)
    joined_at = Column(DateTime, default=func.now())
    last_active = Column(DateTime, default=func.now())
    points = Column(Integer, default=0)
    level = Column(String, default="Suscriptor Íntimo")  # Nivel inicial
    weekly_streak = Column(Integer, default=0)
    monthly_streak = Column(Integer, default=0)
    last_point_date = Column(DateTime)
    referred_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    is_admin = Column(Boolean, default=False)

    point_logs = relationship('PointLog', back_populates='user')
    achievements = relationship('Achievement', back_populates='user')

class PointLog(Base):
    __tablename__ = 'point_logs'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    points = Column(Integer)
    action_type = Column(String)  # 'interaction', 'purchase', 'streak_bonus', etc.
    description = Column(String, nullable=True)
    timestamp = Column(DateTime, default=func.now())

    user = relationship('User', back_populates='point_logs')

class Achievement(Base):
    __tablename__ = 'achievements'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    name = Column(String)
    unlocked_at = Column(DateTime, default=func.now())

    user = relationship('User', back_populates='achievements')

# Puedes agregar aquí otros modelos necesarios para misiones, recompensas, etc.
# Ejemplo:
# class Mission(Base): ...
# class Reward(Base): ...
