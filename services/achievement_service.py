from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import Achievement, User
import datetime
import logging

logger = logging.getLogger(__name__)

# Define aquí todos los logros (puedes expandir con lógica dinámica después)
ACHIEVEMENTS = [
    {
        "name": "Veterano Íntimo",
        "check": lambda user: user.created_at and (datetime.datetime.now() - user.created_at).days >= 180
    },
    {
        "name": "Big Spender VIP",
        "check": lambda user: user.points >= 500
    },
    {
        "name": "Fan Leal Apasionado",
        "check": lambda user: hasattr(user, "point_logs") and len(user.point_logs) >= 50
    },
    # Agrega aquí más logros según la lógica del reporte
]

async def check_and_award_achievements(session: AsyncSession, user: User):
    """
    Checa todos los logros posibles y otorga los que el usuario no tenga.
    Llama esto cada vez que el usuario gana puntos o realiza una acción clave.
    """
    awarded = []
    for ach in ACHIEVEMENTS:
        # Checar si ya tiene el logro
        result = await session.execute(
            select(Achievement).where(
                Achievement.user_id == user.id,
                Achievement.name == ach["name"]
            )
        )
        existing = result.scalar()
        if not existing and ach["check"](user):
            new_ach = Achievement(
                user_id=user.id,
                name=ach["name"],
                unlocked_at=datetime.datetime.now()
            )
            session.add(new_ach)
            await session.commit()
            awarded.append(ach["name"])
            logger.info(f"Logro otorgado: {ach['name']} al usuario {user.id}")
    return awarded  # Lista de nombres de logros nuevos, por si quieres notificarlos

async def get_achievements(session: AsyncSession, user_id: int):
    result = await session.execute(
        select(Achievement).where(Achievement.user_id == user_id)
    )
    return result.scalars().all()
