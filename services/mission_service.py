import datetime
import random
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import User
from services.point_service import PointService

class MissionService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.point_service = PointService(session)

    async def get_user_by_telegram_id(self, telegram_id: int) -> User | None:
        """Obtiene un usuario por su ID de Telegram."""
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def claim_daily_mission(self, telegram_id: int) -> tuple[bool, int | datetime.timedelta]:
        """
        Permite al usuario reclamar su misión diaria.
        Retorna (True, puntos_obtenidos) si se reclamó con éxito.
        Retorna (False, tiempo_restante) si ya la reclamó y aún no pasaron 24h.
        """
        user = await self.get_user_by_telegram_id(telegram_id)
        if not user:
            # Esto no debería pasar si el middleware de registro está funcionando
            return False, 0

        now = datetime.datetime.now()
        if user.last_daily_mission_claim:
            time_since_last_claim = now - user.last_daily_mission_claim
            if time_since_last_claim < datetime.timedelta(hours=24):
                time_remaining = datetime.timedelta(hours=24) - time_since_last_claim
                return False, time_remaining

        # Generar puntos aleatorios para la misión diaria
        points_awarded = random.randint(50, 100)

        # Añadir puntos al usuario
        await self.point_service.add_points(telegram_id, points_awarded)

        # Actualizar la última fecha de reclamo
        user.last_daily_mission_claim = now
        await self.session.commit()
        await self.session.refresh(user)

        return True, points_awarded

    # Puedes añadir más lógicas de misiones aquí
    # Por ejemplo, misiones semanales, logros, etc.
    
