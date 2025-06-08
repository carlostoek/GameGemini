from sqlalchemy import Column, Integer, String, BigInteger, DateTime, Boolean, JSON, Text, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(AsyncAttrs, Base):
    __tablename__ = "users"
    id = Column(BigInteger, primary_key=True, unique=True)  # Telegram User ID
    telegram_id = Column(BigInteger, unique=True) # Redundant with id, but keep for clarity
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    points = Column(Integer, default=0)
    level_id = Column(Integer, ForeignKey('levels.id'), default=1)  # Foreign Key to Level
    level = relationship("Level", back_populates="users")
    join_date = Column(DateTime, default=func.now())
    last_permanence_award_date = Column(DateTime, nullable=True)
    permanence_streak_weeks = Column(Integer, default=0)
    total_spent_mxn = Column(Float, default=0.0)
    total_purchases = Column(Integer, default=0)
    last_renewal_date = Column(DateTime, nullable=True)
    is_auto_renew = Column(Boolean, default=False)
    referred_by_user_id = Column(BigInteger, ForeignKey('users.id'), nullable=True)
    referrer = relationship("User", remote_side=[id], back_populates="referrals") # Self-referential relationship
    referrals = relationship("User", remote_side=[referred_by_user_id], back_populates="referrer")
    channel_reactions = Column(JSON, default={})  # {'message_id': True, 'message_id_2': True}
    total_reactions = Column(Integer, default=0)
    total_poll_participations = Column(Integer, default=0)
    reaction_streak_days = Column(Integer, default=0)

    achievements = Column(JSON, default={})  # {'achievement_id': timestamp_isoformat} # Deprecate in favor of UserBadge?
    missions_completed = Column(JSON, default={})  # {'mission_id': timestamp_isoformat} # Deprecate in favor of UserMission?
    last_daily_mission_reset = Column(DateTime, default=func.now())
    last_weekly_mission_reset = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    badges = relationship("UserBadge", back_populates="user")
    purchases = relationship("Purchase", back_populates="user")
    redemptions = relationship("Redemption", back_populates="user")
    missions = relationship("UserMission", back_populates="user")


    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', points={self.points}, level={self.level_id})>"


class Level(AsyncAttrs, Base):
    __tablename__ = "levels"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    min_points = Column(Integer, nullable=False)
    max_points = Column(Integer, nullable=False)
    benefits_description = Column(Text, nullable=True) # Store benefits as text
    users = relationship("User", back_populates="level") # One-to-many with User

    def __repr__(self):
        return f"<Level(id={self.id}, name='{self.name}', min_points={self.min_points}, max_points={self.max_points})>"


class Badge(AsyncAttrs, Base):
    __tablename__ = "badges"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text)
    unlock_criteria = Column(Text, nullable=True) # Store unlock criteria as text
    image_url = Column(String, nullable=True) # Optional URL for image
    users = relationship("UserBadge", back_populates="badge") # One-to-many with UserBadge

    def __repr__(self):
         return f"<Badge(id={self.id}, name='{self.name}')>"


class UserBadge(AsyncAttrs, Base):
    __tablename__ = "user_badges"
    user_id = Column(BigInteger, ForeignKey('users.id'), primary_key=True)
    badge_id = Column(Integer, ForeignKey('badges.id'), primary_key=True)
    unlocked_date = Column(DateTime, default=func.now())
    user = relationship("User", back_populates="badges")
    badge = relationship("Badge", back_populates="users")

    def __repr__(self):
        return f"<UserBadge(user_id={self.user_id}, badge_id={self.badge_id})>"

class Purchase(AsyncAttrs, Base):
    __tablename__ = "purchases"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    user = relationship("User", back_populates="purchases")
    amount_mxn = Column(Float, nullable=False)
    points_awarded = Column(Integer, nullable=False)
    purchase_date = Column(DateTime, default=func.now())
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False) # Foreign Key to Product
    product = relationship("Product")

    def __repr__(self):
        return f"<Purchase(id={self.id}, user_id={self.user_id}, amount={self.amount_mxn})>"

class Product(AsyncAttrs, Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    price_mxn = Column(Float, nullable=False)
    base_points = Column(Integer, nullable=False)

    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', price={self.price_mxn}, points={self.base_points})>"

class Redemption(AsyncAttrs, Base):
    __tablename__ = "redemptions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    user = relationship("User", back_populates="redemptions")
    benefit_id = Column(Integer, ForeignKey('benefits.id'), nullable=False)
    benefit = relationship("Benefit")
    redemption_date = Column(DateTime, default=func.now())
    status = Column(String, default="pending")  # "pending", "completed", "failed"

    def __repr__(self):
        return f"<Redemption(id={self.id}, user_id={self.user_id}, benefit_id={self.benefit_id}, status='{self.status}')>"


class Benefit(AsyncAttrs, Base):
    __tablename__ = "benefits"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text)
    cost_points = Column(Integer, nullable=False)
    type = Column(String, nullable=False) # "manual", "auto"
    stock = Column(Integer, default=-1)  # -1 for unlimited
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())

    def __repr__(self):
        return f"<Benefit(id={self.id}, name='{self.name}', cost_points={self.cost_points}, type='{self.type}')>"

class UserMission(AsyncAttrs, Base):
    __tablename__ = "user_missions"
    user_id = Column(BigInteger, ForeignKey('users.id'), primary_key=True)
    mission_id = Column(String, ForeignKey('missions.id'), primary_key=True)
    user = relationship("User", back_populates="missions")
    mission = relationship("Mission")
    is_completed = Column(Boolean, default=False)
    completion_date = Column(DateTime, nullable=True)
    progress_data = Column(JSON, nullable=True)  # For missions with progress tracking

    def __repr__(self):
        return f"<UserMission(user_id={self.user_id}, mission_id='{self.mission_id}', is_completed={self.is_completed})>"

class Event(AsyncAttrs, Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    multiplier = Column(Integer, default=1)  # e.g., 2 for double points
    is_active = Column(Boolean, default=True)
    start_time = Column(DateTime, default=func.now())
    end_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    # Add a relationship to track participating users (optional, if needed for leaderboards or specific event logic)
    # participants = relationship("User", secondary="event_participants", back_populates="events")

    def __repr__(self):
        return f"<Event(id={self.id}, name='{self.name}', multiplier={self.multiplier})>"

# Optional table for a many-to-many relationship between Event and User, if you need to track participation explicitly
# class EventParticipant(AsyncAttrs, Base):
#     __tablename__ = "event_participants"
#     user_id = Column(BigInteger, ForeignKey('users.id'), primary_key=True)
#     event_id = Column(Integer, ForeignKey('events.id'), primary_key=True)
#     join_time = Column(DateTime, default=func.now()) # Optional: track when the user joined the event
