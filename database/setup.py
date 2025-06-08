import enum from datetime import datetime from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Enum as SAEnum, UniqueConstraint from sqlalchemy.orm import relationship from .setup import Base

class SourceType(enum.Enum): PERMANENCE = "permanence" REACTION = "reaction" PURCHASE = "purchase" MISSION = "mission" ACHIEVEMENT = "achievement"

class User(Base): tablename = 'users'

id = Column(Integer, primary_key=True)
telegram_id = Column(String, unique=True, nullable=False)
username = Column(String, nullable=True)
join_date = Column(DateTime, default=datetime.utcnow, nullable=False)

points = Column(Integer, default=0)
level = Column(Integer, default=0)

purchases = relationship('Purchase', back_populates='user')
referrals_made = relationship('Referral', foreign_keys='Referral.referrer_id', back_populates='referrer')
referrals_received = relationship('Referral', foreign_keys='Referral.referred_id', back_populates='referred')
point_history = relationship('PointHistory', back_populates='user')
achievements = relationship('Achievement', back_populates='user')
redemptions = relationship('RedemptionHistory', back_populates='user')

class Purchase(Base): tablename = 'purchases'

id = Column(Integer, primary_key=True)
user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
amount = Column(Float, nullable=False)
date = Column(DateTime, default=datetime.utcnow, nullable=False)
points_awarded = Column(Integer, nullable=False)

user = relationship('User', back_populates='purchases')

class Referral(Base): tablename = 'referrals'

id = Column(Integer, primary_key=True)
referrer_id = Column(Integer, ForeignKey('users.id'), nullable=False)
referred_id = Column(Integer, ForeignKey('users.id'), nullable=False)
date = Column(DateTime, default=datetime.utcnow, nullable=False)

referrer = relationship('User', foreign_keys=[referrer_id], back_populates='referrals_made')
referred = relationship('User', foreign_keys=[referred_id], back_populates='referrals_received')

__table_args__ = (
    UniqueConstraint('referrer_id', 'referred_id', name='uq_referral_pair'),
)

class PointHistory(Base): tablename = 'point_history'

id = Column(Integer, primary_key=True)
user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
source_type = Column(SAEnum(SourceType), nullable=False)
source_id = Column(String, nullable=True)
points = Column(Integer, nullable=False)
timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

user = relationship('User', back_populates='point_history')

class Achievement(Base): tablename = 'achievements'

id = Column(Integer, primary_key=True)
user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
name = Column(String, nullable=False)
date_awarded = Column(DateTime, default=datetime.utcnow, nullable=False)

user = relationship('User', back_populates='achievements')

class Reward(Base): tablename = 'rewards'

id = Column(Integer, primary_key=True)
name = Column(String, unique=True, nullable=False)
cost_points = Column(Integer, nullable=False)
description = Column(String, nullable=True)

class RedemptionHistory(Base): tablename = 'redemption_history'

id = Column(Integer, primary_key=True)
user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
reward_id = Column(Integer, ForeignKey('rewards.id'), nullable=False)
date = Column(DateTime, default=datetime.utcnow, nullable=False)

user = relationship('User', back_populates='redemptions')
reward = relationship('Reward')

