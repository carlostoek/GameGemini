# database/models.py

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Reward(Base):
    __tablename__ = "rewards"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    points_required = Column(Integer, nullable=False)

    def __repr__(self):
        return f"<Reward(id={self.id}, name={self.name}, points_required={self.points_required})>"
