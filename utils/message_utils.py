# utils/message_utils.py
from database.models import User, Mission, Reward
from services.level_service import get_level_threshold
from services.achievement_service import ACHIEVEMENTS
from utils.messages import BOT_MESSAGES
import datetime

async def get_profile_message(user: User, active_missions: list[Mission]) -> str:
    points_to_next_level_text = ""
    next_level_threshold = get_level_threshold(user.level + 1)
    if next_level_threshold != float('inf'):
        points_needed = next_level_threshold - user.points
        # Usar el mensaje personalizado para puntos al siguiente nivel
        points_to_next_level_text = BOT_MESSAGES["profile_points_to_next_level"].format(
            points_needed=points_needed,
            next_level=user.level + 1,
            next_level_threshold=next_level_threshold
        )
    else:
        # Usar el mensaje personalizado para nivel máximo
        points_to_next_level_text = BOT_MESSAGES["profile_max_level"]


    # Usar el mensaje personalizado para no logros
    achievements_text = BOT_MESSAGES["profile_no_achievements"]
    if user.achievements:
        granted_achievements_list = []
        for ach_id, timestamp_str in user.achievements.items():
            if ach_id in ACHIEVEMENTS:
                granted_achievements_list.append({
                    "id": ach_id,
                    "name": ACHIEVEMENTS[ach_id].get("name", ach_id),
                    "icon": ACHIEVEMENTS[ach_id].get("icon", ""),
                    "granted_at": timestamp_str
                })
        # Ordenar logros por fecha de concesión si es necesario
        granted_achievements_list.sort(key=lambda x: x['granted_at'])
        
        achievements_list = [
            f"{ach['icon']} {ach['name']} (Desbloqueado el: {datetime.datetime.fromisoformat(ach['granted_at']).strftime('%d/%m/%Y')})"
            for ach in granted_achievements_list
        ]
        achievements_text = BOT_MESSAGES["profile_achievements_title"] + "\n" + "\n".join(achievements_list)


    # Usar el mensaje personalizado para no misiones activas
    missions_text = BOT_MESSAGES["profile_no_active_missions"]
    if active_missions:
        missions_list = [
            f"• {mission.name} ({mission.points_reward} Puntos)"
            for mission in active_missions
        ]
        missions_text = BOT_MESSAGES["profile_active_missions_title"] + "\n" + "\n".join(missions_list)

    return (
        # Usar mensajes personalizados para cada parte del perfil
        f"{BOT_MESSAGES['profile_title']}\n\n"
        f"{BOT_MESSAGES['profile_points'].format(user_points=user.points)}\n"
        f"{BOT_MESSAGES['profile_level'].format(user_level=user.level)}\n"
        f"{points_to_next_level_text}\n\n"
        f"{achievements_text}\n\n" # Incluye el título de logros
        f"{missions_text}" # Incluye el título de misiones
    )

async def get_mission_details_message(mission: Mission) -> str:
    # Usar el mensaje personalizado para detalles de misión
    return BOT_MESSAGES["mission_details_text"].format(
        mission_name=mission.name,
        mission_description=mission.description,
        points_reward=mission.points_reward,
        mission_type=mission.type.capitalize()
    )

async def get_reward_details_message(reward: Reward, user_points: int) -> str:
    stock_info = ""
    if reward.stock != -1:
        stock_info = BOT_MESSAGES["reward_details_stock_info"].format(stock_left=reward.stock)
    else:
        stock_info = BOT_MESSAGES["reward_details_no_stock_info"]

    # Usar el mensaje personalizado para detalles de recompensa
    return BOT_MESSAGES["reward_details_text"].format(
        reward_name=reward.name,
        reward_description=reward.description,
        reward_cost=reward.cost,
        stock_info=stock_info
    )

async def get_ranking_message(users_ranking: list[User]) -> str:
    """
    Generates a formatted message for the user ranking.
    """
    ranking_text = BOT_MESSAGES["ranking_title"] + "\n\n"

    if not users_ranking:
        return ranking_text + BOT_MESSAGES["no_ranking_data"]

    for i, user in enumerate(users_ranking):
        # Format each user entry
        # Usa user.username si está disponible, de lo contrario, user.first_name
        display_name = user.username if user.username else user.first_name if user.first_name else "Usuario Desconocido"
        ranking_text += BOT_MESSAGES["ranking_entry"].format(
            rank=i + 1,
            username=display_name,
            points=user.points,
            level=user.level
        ) + "\n"

    return ranking_text

