# services/point_service.py

import datetime
from sqlalchemy import select, update, func
from database.models import User, PointLog
from services.level_service import get_level_by_points
from services.achievement_service import check_and_award_achievements

# --- CONFIGURACIÓN DE LÍMITES ---
DAILY_LIMIT = 20  # Máx. puntos por día (personalizable)
WEEKLY_LIMIT = 120  # Máx. puntos por semana (personalizable)

BONUS_WEEKLY_STREAK = [0, 11, 12, 13, 14, 15]  # +10...+15 por racha semanal
BONUS_MONTHLY = 50  # Bonus por cada mes
BONUS_6MONTHS = 100
BONUS_1YEAR = 200

async def get_today():
    return datetime.datetime.now().date()

async def can_receive_points(session, user_id, points, action_type="interaction"):
    today = await get_today()
    week_start = today - datetime.timedelta(days=today.weekday())
    # Total diario
    result = await session.execute(
        select(func.sum(PointLog.points)).where(
            PointLog.user_id == user_id,
            PointLog.action_type == action_type,
            func.date(PointLog.timestamp) == today
        )
    )
    day_total = result.scalar() or 0
    if day_total + points > DAILY_LIMIT:
        return False, DAILY_LIMIT - day_total
    # Total semanal
    result = await session.execute(
        select(func.sum(PointLog.points)).where(
            PointLog.user_id == user_id,
            PointLog.action_type == action_type,
            func.date(PointLog.timestamp) >= week_start,
            func.date(PointLog.timestamp) <= today
        )
    )
    week_total = result.scalar() or 0
    if week_total + points > WEEKLY_LIMIT:
        return False, WEEKLY_LIMIT - week_total
    return True, points

async def add_points(session, user_id, points, action_type="interaction", description=None, forced=False):
    """
    Asigna puntos a un usuario, respetando límites diarios/semanales.
    forced=True ignora límites (para compras/admin).
    """
    if not forced:
        allowed, allowed_points = await can_receive_points(session, user_id, points, action_type)
        if not allowed:
            return False, f"Limite diario/semanal alcanzado. Solo puedes recibir {allowed_points} puntos más hoy."
        points = allowed_points if allowed_points < points else points

    user = await session.get(User, user_id)
    if not user:
        return False, "Usuario no encontrado."

    user.points += points

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

    # Actualizar nivel
    new_level = await get_level_by_points(user.points)
    if user.level != new_level:
        user.level = new_level
        await session.commit()

    # Check logros/insignias
    await check_and_award_achievements(session, user)

    return True, f"¡Has recibido {points} puntos! Total: {user.points}"

# --- Bonificaciones por racha y permanencia ---

async def award_weekly_bonus(session, user):
    streak = user.weekly_streak or 1
    bonus = BONUS_WEEKLY_STREAK[min(streak, len(BONUS_WEEKLY_STREAK)-1)]
    user.points += bonus
    user.weekly_streak = streak + 1 if streak < 5 else 1
    session.add(PointLog(
        user_id=user.id,
        points=bonus,
        action_type="streak_bonus",
        description=f"Bonus por racha semanal {streak}",
        timestamp=datetime.datetime.now()
    ))
    await session.commit()
    await check_and_award_achievements(session, user)
    return bonus

async def award_monthly_bonus(session, user):
    user.points += BONUS_MONTHLY
    session.add(PointLog(
        user_id=user.id,
        points=BONUS_MONTHLY,
        action_type="month_bonus",
        description="Bonus por permanencia mensual",
        timestamp=datetime.datetime.now()
    ))
    await session.commit()
    await check_and_award_achievements(session, user)
    return BONUS_MONTHLY

async def award_hito_bonus(session, user, months):
    # Bonus por 6 meses y 1 año
    if months >= 12:
        user.points += BONUS_1YEAR
        desc = "Bonus por 1 año de permanencia"
        points = BONUS_1YEAR
    elif months >= 6:
        user.points += BONUS_6MONTHS
        desc = "Bonus por 6 meses de permanencia"
        points = BONUS_6MONTHS
    else:
        return 0
    session.add(PointLog(
        user_id=user.id,
        points=points,
        action_type="hito_bonus",
        description=desc,
        timestamp=datetime.datetime.now()
    ))
    await session.commit()
    await check_and_award_achievements(session, user)
    return points

# --- Asignación por compras/admin ---

async def add_points_by_admin(session, user_id, points, description="Compra/Admin"):
    # Ignora límites diarios/semanales
    return await add_points(session, user_id, points, action_type="purchase", description=description, forced=True)
