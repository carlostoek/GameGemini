from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User
import datetime

# Definición de logros (ejemplo)
ACHIEVEMENTS = {
    "first_mission": {"name": "Primera Misión Completada", "icon": "🏅"},
    "level_5": {"name": "Maestro Principiante (Nivel 5)", "icon": "⭐"},
    "daily_streak_3": {"name": "Racha Diaria (3 Días)", "icon": "🔥"}, # Requires scheduling outside
    "first_purchase": {"name": "Primer Comprador", "icon": "💰"},
    "trivia_master": {"name": "Experto en Trivias", "icon": "🧠"}, # Requires trivia system
    "contributor": {"name": "Colaborador Activo", "icon": "🤝"} # Requires more complex engagement
}

class AchievementService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def grant_achievement(self, user_id: int, achievement_id: str) -> bool:
        user = await self.session.get(User, user_id)
        if not user:
            return False

        if achievement_id not in user.achievements:
            user.achievements[achievement_id] = datetime.datetime.now().isoformat()
            await self.session.commit()
            await self.session.refresh(user)
            return True
        return False

    async def get_user_achievements(self, user_id: int) -> dict:
        user = await self.session.get(User, user_id)
        if not user:
            return {}
        granted_achievements = {}
        for ach_id, timestamp_str in user.achievements.items():
            if ach_id in ACHIEVEMENTS:
                # Create a mutable copy of the achievement data
                ach_data = ACHIEVEMENTS[ach_id].copy()
                ach_data['granted_at'] = timestamp_str # Store as ISO format string
                granted_achievements[ach_id] = ach_data
        return granted_achievements
