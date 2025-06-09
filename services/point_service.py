# services/point_service.py

import logging
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import User

# Configuramos el logger estándar de Python
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class PointService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_points(self, user_id: int, points: int) -> Optional[User]:
        """
        Suma (o resta, si points es negativo) puntos al usuario.
        Crea usuario si no existe.
        """
        user = await self.session.get(User, user_id)
        if not user:
            user = User(id=user_id, username="SinUsername", points=0)
            self.session.add(user)
        user.points = (user.points or 0) + points
        await self.session.commit()
        await self.session.refresh(user)
        logger.info(f"User {user_id} points changed by {points}. Total: {user.points}")
        return user

    async def deduct_points(self, user_id: int, points: int) -> Optional[User]:
        """
        Resta puntos al usuario si tiene saldo suficiente.
        """
        user = await self.session.get(User, user_id)
        if user and (user.points or 0) >= points:
            user.points -= points
            await self.session.commit()
            await self.session.refresh(user)
            logger.info(f"User {user_id} lost {points} points. Total: {user.points}")
            return user

        logger.warning(f"Failed to deduct {points} points from user {user_id}. Not enough points or user not found.")
        return None

    async def get_user_points(self, user_id: int) -> int:
        """
        Retorna el total de puntos del usuario.
        """
        user = await self.session.get(User, user_id)
        return user.points if user else 0

# ——— Atajos globales para importación fácil ———

async def add_points(session: AsyncSession, user_id: int, points: int) -> Optional[User]:
    return await PointService(session).add_points(user_id, points)

async def get_user_points(session: AsyncSession, user_id: int) -> int:
    return await PointService(session).get_user_points(user_id)

async def get_top_users(session: AsyncSession, limit: int = 10) -> List[User]:
    """
    Retorna la lista de los 'limit' usuarios con más puntos.
    """
    stmt = select(User).order_by(User.points.desc()).limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all()

async def record_purchase(session: AsyncSession, user_id: int, reward_id: int) -> bool:
    """
    Registra la compra de una recompensa (placeholder).
    """
    logger.info(f"Recording purchase: user {user_id}, reward {reward_id}")
    return True
