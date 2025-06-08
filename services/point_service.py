from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from database.models import User, PointLog
import logging
import datetime

logger = logging.getLogger(__name__)

# --- FUNCIONES DE SERVICIO DE PUNTOS ---

async def add_points(session: AsyncSession, user_id: int, points: int, action_type="interaction", description=None, forced=False) -> User:
    """
    Suma puntos a un usuario, registra la acción en PointLog y devuelve el usuario actualizado.
    action_type: 'interaction', 'purchase', 'mission', etc.
    forced: si es True ignora límites diarios/semanales (para compras/admin)
    """
    user = await session.get(User, user_id)
    if not user:
        # Si el usuario no existe, lo crea como placeholder (mejor crearlo con /start en producción)
        logger.warning(f"Attempted to add points to non-existent user {user_id}. Creating new user.")
        user = User(id=user_id, points=0)
        session.add(user)
        await session.commit()
        await session.refresh(user)

    user.points += points
    user.updated_at = datetime.datetime.now()

    # Registrar log
    log = PointLog(
        user_id=user_id,
        points=points,
        action_type=action_type,
        description=description,
        timestamp=datetime.datetime.now()
    )
    session.add(log)

    await session.commit()
    await session.refresh(user)
    logger.info(f"User {user_id} gained {points} points. Total: {user.points}")
    return user

async def deduct_points(session: AsyncSession, user_id: int, points: int, action_type="admin_deduct", description=None) -> User | None:
    user = await session.get(User, user_id)
    if not user:
        logger.warning(f"Attempted to deduct points from non-existent user {user_id}.")
        return None
    user.points = max(0, user.points - points)
    user.updated_at = datetime.datetime.now()
    # Registrar log negativo (opcional)
    log = PointLog(
        user_id=user_id,
        points=-abs(points),
        action_type=action_type,
        description=description or "Puntos restados por admin",
        timestamp=datetime.datetime.now()
    )
    session.add(log)
    await session.commit()
    await session.refresh(user)
    logger.info(f"User {user_id} lost {points} points. Total: {user.points}")
    return user

async def get_points(session: AsyncSession, user_id: int) -> int:
    user = await session.get(User, user_id)
    return user.points if user else 0

async def get_point_logs(session: AsyncSession, user_id: int, limit: int = 20):
    stmt = select(PointLog).where(PointLog.user_id == user_id).order_by(PointLog.timestamp.desc()).limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all()

# Puedes agregar aquí cualquier otra función utilitaria de puntos que necesites,
# por ejemplo, sumar por tipo de acción, sumar en un rango de fechas, etc.
