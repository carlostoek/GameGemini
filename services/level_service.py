from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User
import math

# Definición de costos de nivel
# Key: current level, Value: points needed to reach this level from level 1
# This table defines the CUMULATIVE points needed to reach a level.
# Or, simpler: points needed to pass to the NEXT level.
# Let's adjust this to be points *needed to reach the NEXT level*.
# So, to reach Level 2, you need 10 points. To reach Level 3, you need 25 (total from start).
LEVEL_THRESHOLDS = {
    1: 0,   # Already at level 1 with 0 points
    2: 10,  # Need 10 points to reach level 2
    3: 25,  # Need 25 points to reach level 3
    4: 50,
    5: 100,
    6: 200,
    7: 350,
    8: 550,
    9: 800,
    10: 1100,
    # Add more levels as needed
}

def get_level_threshold(level: int) -> int:
    """Returns the cumulative points needed to reach the given level."""
    return LEVEL_THRESHOLDS.get(level, float('inf')) # Return infinity if level is beyond defined

class LevelService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def check_for_level_up(self, user: User) -> bool:
        """
        Checks if the user has enough points to level up.
        Updates user's level if so, and returns True.
        Can level up multiple times if points allow.
        """
        leveled_up = False
        while True:
            next_level = user.level + 1
            points_for_next_level = get_level_threshold(next_level)

            if points_for_next_level == float('inf'): # Max level reached
                break

            if user.points >= points_for_next_level:
                user.level = next_level
                leveled_up = True
            else:
                break
        if leveled_up:
            await self.session.commit()
            await self.session.refresh(user)
        return leveled_up

    async def get_user_level(self, user_id: int) -> int:
        user = await self.session.get(User, user_id)
        return user.level if user else 1

    async def get_level_progress(self, user: User) -> tuple[int, int]:
        """
        Returns (current_points_in_level, points_to_next_level_from_current_level)
        """
        current_level_threshold = get_level_threshold(user.level)
        next_level_threshold = get_level_threshold(user.level + 1)

        if next_level_threshold == float('inf'): # Max level reached
            return user.points, 0 # Indicate maxed out, 0 points to next level

        points_needed_for_next_level = next_level_threshold - user.points
        return user.points, points_needed_for_next_level

