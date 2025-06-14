from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from database.models import User
import logging

logger = logging.getLogger(__name__)

class PointService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_points(self, user_id: int, points: int) -> User:
        user = await self.session.get(User, user_id)
        if not user:
            # If user somehow doesn't exist, create a placeholder.
            # In a real bot, user should be created on /start.
            logger.warning(f"Attempted to add points to non-existent user {user_id}. Creating new user.")
            user = User(id=user_id, points=0) # Initialize with 0 points
            self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)

        user.points += points
        await self.session.commit()
        await self.session.refresh(user)
        logger.info(f"User {user_id} gained {points} points. Total: {user.points}")
        return user

    async def deduct_points(self, user_id: int, points: int) -> User | None:
        user = await self.session.get(User, user_id)
        if user and user.points >= points:
            user.points -= points
            await self.session.commit()
            await self.session.refresh(user)
            logger.info(f"User {user_id} lost {points} points. Total: {user.points}")
            return user
        logger.warning(f"Failed to deduct {points} points from user {user_id}. Not enough points or user not found.")
        return None

    async def get_user_points(self, user_id: int) -> int:
        user = await self.session.get(User, user_id)
        return user.points if user else 0

    async def get_top_users(self, limit: int = 10) -> list[User]:
        """Return the top users ordered by points."""
        stmt = select(User).order_by(User.points.desc()).limit(limit)
        result = await self.session.execute(stmt)
        top_users = result.scalars().all()
        return top_users
