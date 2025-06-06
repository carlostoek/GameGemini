from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from database.models import Mission, User
import datetime
import logging

logger = logging.getLogger(__name__)

class MissionService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_active_missions(self, user_id: int = None, mission_type: str = None) -> list[Mission]:
        stmt = select(Mission).where(Mission.is_active == True)
        if mission_type:
            stmt = stmt.where(Mission.type == mission_type)
        result = await self.session.execute(stmt)
        missions = result.scalars().all()

        if user_id: # Filter out completed missions for a specific user based on reset rules
            user = await self.session.get(User, user_id)
            if user:
                filtered_missions = []
                now = datetime.datetime.now()

                for mission in missions:
                    is_completed_for_period = False
                    if mission.id in user.missions_completed:
                        completed_at_str = user.missions_completed[mission.id]
                        completed_at = datetime.datetime.fromisoformat(completed_at_str)

                        if mission.type == 'daily':
                            # Mission is completed if it was done less than 24 hours ago
                            if (now - completed_at).total_seconds() < 24 * 3600:
                                is_completed_for_period = True
                        elif mission.type == 'weekly':
                            # Mission is completed if it was done less than 7 days ago
                            if (now - completed_at).total_seconds() < 7 * 24 * 3600:
                                is_completed_for_period = True
                        elif mission.type == 'one_time':
                            is_completed_for_period = True # One-time missions stay completed

                    if not is_completed_for_period:
                        filtered_missions.append(mission)
                return filtered_missions
        return missions

    async def complete_mission(self, user_id: int, mission_id: str) -> tuple[bool, Mission | None]:
        user = await self.session.get(User, user_id)
        mission = await self.session.get(Mission, mission_id)

        if not user or not mission or not mission.is_active:
            return False, None

        now = datetime.datetime.now()
        is_already_completed_for_period = False

        if mission.id in user.missions_completed:
            completed_at_str = user.missions_completed[mission.id]
            completed_at = datetime.datetime.fromisoformat(completed_at_str)

            if mission.type == 'daily':
                if (now - completed_at).total_seconds() < 24 * 3600:
                    is_already_completed_for_period = True
            elif mission.type == 'weekly':
                if (now - completed_at).total_seconds() < 7 * 24 * 3600:
                    is_already_completed_for_period = True
            elif mission.type == 'one_time':
                is_already_completed_for_period = True

        if is_already_completed_for_period:
            logger.info(f"User {user_id} tried to complete mission {mission_id} again, but it's already completed for the period.")
            return False, mission

        # Mark mission as completed for the user
        user.missions_completed[mission.id] = now.isoformat() # Store as ISO string

        # Update last reset timestamps for the user
        if mission.type == 'daily':
            user.last_daily_mission_reset = now
        elif mission.type == 'weekly':
            user.last_weekly_mission_reset = now

        await self.session.commit()
        await self.session.refresh(user)
        logger.info(f"User {user_id} successfully completed mission {mission_id}.")
        return True, mission

    async def create_mission(self, name: str, description: str, points_reward: int, mission_type: str, requires_action: bool = False, action_data: dict = None) -> Mission:
        mission_id = f"{mission_type}_{name.lower().replace(' ', '_').replace('.', '').replace(',', '')}" # Simple ID generation
        new_mission = Mission(
            id=mission_id,
            name=name,
            description=description,
            points_reward=points_reward,
            type=mission_type,
            is_active=True,
            requires_action=requires_action,
            action_data=action_data
        )
        self.session.add(new_mission)
        await self.session.commit()
        await self.session.refresh(new_mission)
        return new_mission

    async def toggle_mission_status(self, mission_id: str, status: bool) -> bool:
        mission = await self.session.get(Mission, mission_id)
        if mission:
            mission.is_active = status
            await self.session.commit()
            return True
        return False
