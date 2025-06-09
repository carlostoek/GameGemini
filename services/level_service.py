# services/level_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import User
import math

# Definición de puntos necesarios para cada nivel
LEVEL_THRESHOLDS = {
    1: 0,
    2: 10,
    3: 25,
    4: 50,
    5: 100,
    # Añade más niveles según sea necesario
}

def get_level_threshold(level: int) -> int:
    """
    Devuelve los puntos acumulativos necesarios para alcanzar el nivel dado.
    Si el nivel no existe en el diccionario, devuelve infinito.
    """
    return LEVEL_THRESHOLDS.get(level, math.inf)

async def get_user_level(session: AsyncSession, user_id: int) -> int:
    """
    Retorna el nivel actual del usuario basado en sus puntos.
    """
    result = await session.execute(select(User.points).where(User.id == user_id))
    row = result.scalar_one_or_none()
    points = row if row is not None else 0

    # Determinar nivel según thresholds
    level = 1
    for lvl, thresh in sorted(LEVEL_THRESHOLDS.items()):
        if points >= thresh:
            level = lvl
        else:
            break
    return level

async def get_level_progress(session: AsyncSession, user_id: int) -> tuple[int, int]:
    """
    Retorna (puntos_actuales_en_nivel, puntos_para_siguiente_nivel).
    """
    result = await session.execute(select(User.points).where(User.id == user_id))
    row = result.scalar_one_or_none()
    points = row if row is not None else 0

    current_level = await get_user_level(session, user_id)
    current_threshold = get_level_threshold(current_level)
    next_threshold = get_level_threshold(current_level + 1)

    if next_threshold == math.inf:
        return points - current_threshold, 0

    return points - current_threshold, next_threshold - points
    
