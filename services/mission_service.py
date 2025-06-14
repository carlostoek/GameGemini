# services/mission_service.py
import datetime
import random
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from database.models import Mission, User
import logging

logger = logging.getLogger(__name__)

class MissionService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_active_missions(self, user_id: int = None, mission_type: str = None) -> list[Mission]:
        """
        Retrieves active missions, optionally filtered by user completion status and type.
        """
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

    async def check_mission_completion_status(self, user: User, mission: Mission, target_message_id: int = None) -> tuple[bool, str]:
        """
        Checks if a user has completed a mission for the current reset period,
        or if it's a one-time mission already completed.
        Returns (is_completed_for_period, reason_if_completed)
        """
        mission_completion_record = user.missions_completed.get(mission.id)
        
        if mission.type == "one_time":
            if mission_completion_record:
                return True, "already_completed"
        elif mission.type == "daily":
            if mission_completion_record:
                last_completed = datetime.datetime.fromisoformat(mission_completion_record)
                if (datetime.datetime.now() - last_completed) < datetime.timedelta(days=1):
                    return True, "daily_limit_reached"
        elif mission.type == "weekly":
            if mission_completion_record:
                last_completed = datetime.datetime.fromisoformat(mission_completion_record)
                if (datetime.datetime.now() - last_completed) < datetime.timedelta(weeks=1):
                    return True, "weekly_limit_reached"
        elif mission.type == "reaction":
            # For reaction missions, check if the specific reaction for that message_id is recorded
            if mission.action_data and mission.action_data.get('target_message_id') == target_message_id:
                if user.channel_reactions and str(target_message_id) in user.channel_reactions:
                    return True, "already_reacted_to_this_message"
            elif mission_completion_record: # If it's a generic reaction mission, check one-time completion
                return True, "already_completed"
        
        return False, "" # Not completed for current period or not a one-time mission

    async def complete_mission(self, user_id: int, mission_id: str, reaction_type: str = None, target_message_id: int = None) -> tuple[bool, Mission | None]:
        """
        Marks a mission as completed for a user, adds points, and handles reset logic.
        Returns (True, mission_object) on success, (False, None) on failure.
        """
        user = await self.session.get(User, user_id)
        mission = await self.session.get(Mission, mission_id)

        if not user or not mission or not mission.is_active:
            logger.warning(f"Failed to complete mission: User {user_id} or mission {mission_id} not found or inactive.")
            return False, None

        # Check if already completed for the current period
        is_completed, reason = await self.check_mission_completion_status(user, mission, target_message_id)
        if is_completed:
            logger.info(f"User {user_id} attempted to complete mission {mission_id} but it was already completed ({reason}).")
            return False, None

        # Add mission to user's completed list with timestamp
        now = datetime.datetime.now().isoformat()
        user.missions_completed[mission.id] = now
        
        # Specific handling for reaction missions: record the message_id for which the reaction was given
        if mission.type == "reaction" and mission.requires_action and target_message_id:
            if not user.channel_reactions:
                user.channel_reactions = {}
            user.channel_reactions[str(target_message_id)] = now  # Record the reaction for this specific message

        # Add points to user. Event multiplier should be handled by PointService or calling context.
        # For simplicity here, we just add the base points.
        # If event multiplier logic is outside this, ensure it's applied before calling add_points.
        # If it's inside PointService, this is fine.
        point_service = self.point_service # assuming point_service is still available in __init__
        if not hasattr(self, 'point_service'): # Fallback if not initialized in __init__
             from services.point_service import PointService
             point_service = PointService(self.session)

        await point_service.add_points(user_id, mission.points_reward)

        # Update last reset timestamps for daily/weekly missions
        if mission.type == "daily":
            user.last_daily_mission_reset = datetime.datetime.now()
        elif mission.type == "weekly":
            user.last_weekly_mission_reset = datetime.datetime.now()
        
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
