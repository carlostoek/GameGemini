# services/mission_service.py
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
                    is_completed_for_period, _ = await self.check_mission_completion_status(user, mission)
                    if not is_completed_for_period:
                        filtered_missions.append(mission)
                return filtered_missions
        return missions

    async def get_mission_by_id(self, mission_id: str) -> Mission | None:
        return await self.session.get(Mission, mission_id)

    async def check_mission_completion_status(self, user: User, mission: Mission, target_message_id: int = None) -> tuple[bool, str | None]:
        """
        Checks if a mission is completed for the current period for a given user.
        Returns (is_completed, completion_id_for_type)
        For 'reaction' missions, completion_id is the message_id.
        """
        now = datetime.datetime.now()

        # Handle 'reaction' missions separately
        if mission.type == 'reaction':
            if target_message_id is None:
                logger.warning(f"check_mission_completion_status called for reaction mission '{mission.id}' without target_message_id.")
                return True, None # Cannot check without target_message_id, assume completed to avoid issues

            # Check if user has already reacted to this specific message_id
            if user.channel_reactions and str(target_message_id) in user.channel_reactions:
                return True, str(target_message_id) # Already reacted to this message
            return False, None # Not reacted to this message yet

        # For other mission types, use the existing logic
        if mission.id in user.missions_completed:
            completed_at_str = user.missions_completed[mission.id]
            completed_at = datetime.datetime.fromisoformat(completed_at_str)

            if mission.type == 'daily':
                if (now - completed_at).total_seconds() < 24 * 3600:
                    return True, mission.id
            elif mission.type == 'weekly':
                # Check if it's within the current week (e.g., Monday to Sunday)
                # This check can be more robust for different week definitions
                start_of_week_completed = completed_at - datetime.timedelta(days=completed_at.weekday())
                start_of_current_week = now - datetime.timedelta(days=now.weekday())
                if start_of_week_completed.date() == start_of_current_week.date():
                    return True, mission.id
            elif mission.type in ['one_time', 'event']:
                # One-time or event missions are completed indefinitely once done
                return True, mission.id
        return False, None


    async def complete_mission(self, user_id: int, mission_id: str, target_message_id: int = None) -> tuple[bool, Mission | None]:
        """
        Marks a mission as completed for a user.
        For 'reaction' missions, target_message_id is required.
        """
        user = await self.session.get(User, user_id)
        mission = await self.session.get(Mission, mission_id)

        if not user or not mission:
            logger.warning(f"Attempted to complete mission {mission_id} for user {user_id}: User or Mission not found.")
            return False, None

        # Check if already completed for the period, with specific logic for 'reaction' type
        is_completed_for_period, _ = await self.check_mission_completion_status(user, mission, target_message_id)
        if is_completed_for_period:
            logger.info(f"Mission {mission_id} for user {user_id} already completed for the current period/message.")
            return False, mission # Already completed

        now = datetime.datetime.now()

        if mission.type == 'reaction':
            if target_message_id is None:
                logger.error(f"Cannot complete reaction mission {mission_id} without target_message_id.")
                return False, None
            # Mark reaction as completed for this specific message_id
            user.channel_reactions[str(target_message_id)] = now.isoformat() # Store timestamp
            # No need to add to user.missions_completed for reaction missions, as they are per-message
            # However, if you want to track if a user has ever completed *any* reaction mission,
            # you might still add a generic entry to missions_completed for the mission ID itself.
            # For now, we'll rely only on channel_reactions for this type.
        else:
            user.missions_completed[mission.id] = now.isoformat() # Store as ISO string

            # Update last reset timestamps for the user
            if mission.type == 'daily':
                user.last_daily_mission_reset = now
            elif mission.type == 'weekly':
                user.last_weekly_mission_reset = now
        
        # Ensure JSON field updates are marked for SQLAlchemy
        self.session.add(user) # Mark user as modified

        await self.session.commit()
        await self.session.refresh(user)
        logger.info(f"User {user_id} successfully completed mission {mission_id} (Type: {mission.type}, Message: {target_message_id}).")
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
                             
