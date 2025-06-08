# services/achievement_service.py

import datetime
from sqlalchemy import select
from database.models import Achievement

# Lista de logros base (puedes expandir)
ACHIEVEMENTS = [
    {"name": "Veterano Íntimo", "condition": lambda user: user.joined_at and (datetime.datetime.now() - user.joined_at).days >= 180},
    {"name": "Big Spender VIP", "condition": lambda user: user.points >= 500},
    {"name": "Fan Leal Apasionado", "condition": lambda user: len(user.point_logs) >= 50},
    # Agrega más logros aquí según sea necesario
]

async def check_and_award_achievements(session, user):
    """
    Verifica y otorga logros al usuario según condiciones definidas.
    """
    for ach in ACHIEVEMENTS:
        # Checar si ya tiene este logro
        result = await session.execute(
            select(Achievement).where(
                Achievement.user_id == user.id,
                Achievement.name == ach["name"]
            )
        )
        existing = result.scalar()
        if not existing and ach["condition"](user):
            # Otorgar logro
            new_ach = Achievement(
                user_id=user.id,
                name=ach["name"],
                unlocked_at=datetime.datetime.now()
            )
            session.add(new_ach)
            await session.commit()
            # Aquí puedes notificar al usuario, si lo deseas (devuelve el nombre del logro)
            # Por ejemplo: return ach["name"]
