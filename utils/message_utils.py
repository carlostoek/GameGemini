from database.models import User, Mission, Reward
from services.level_service import get_level_threshold, LEVEL_THRESHOLDS
from services.achievement_service import ACHIEVEMENTS

async def get_profile_message(user: User, active_missions: list[Mission]) -> str:
    points_to_next_level_text = ""
    next_level_threshold = get_level_threshold(user.level + 1)
    if next_level_threshold != float('inf'):
        points_needed = next_level_threshold - user.points
        points_to_next_level_text = f"📈 **Puntos para el siguiente nivel:** `{points_needed}` (Nivel `{user.level + 1}` requiere `{next_level_threshold}` puntos)\n"
    else:
        points_to_next_level_text = "✨ **¡Has alcanzado el nivel máximo!**\n"


    achievements_text = "No tienes logros aún. ¡Sigue interactuando para desbloquearlos! 🚀"
    if user.achievements:
        # Get actual achievement names and icons, sorted by granted date
        granted_achievements_list = []
        for ach_id, timestamp_str in user.achievements.items():
            if ach_id in ACHIEVEMENTS:
                granted_achievements_list.append({
                    "id": ach_id,
                    "name": ACHIEVEMENTS[ach_id]['name'],
                    "icon": ACHIEVEMENTS[ach_id]['icon'],
                    "granted_at": timestamp_str
                })
        # Sort by granted_at (most recent first)
        granted_achievements_list.sort(key=lambda x: x['granted_at'], reverse=True)

        achievements_formatted = [f"{ach['icon']} `{ach['name']}`" for ach in granted_achievements_list]
        achievements_text = "\n".join(achievements_formatted)


    missions_text = "No tienes misiones activas. ¡Revisa la sección 'Misiones' para nuevas oportunidades! 🎯"
    if active_missions:
        missions_list = [f"- **{mission.name}** (`{mission.points_reward}` Pts)" for mission in active_missions]
        missions_text = "\n".join(missions_list)

    return (
        f"👤 **Tu Perfil de Gamificación, {user.first_name or user.username}**\n\n"
        f"✨ **Puntos Acumulados:** `{user.points}`\n"
        f"🌟 **Nivel Actual:** `{user.level}`\n"
        f"{points_to_next_level_text}\n"
        f"🏆 **Logros Desbloqueados:**\n{achievements_text}\n\n"
        f"🎯 **Misiones Activas:**\n{missions_text}"
    )

async def get_mission_details_message(mission: Mission) -> str:
    return (
        f"🎯 **Misión: {mission.name}**\n\n"
        f"📝 **Descripción:** {mission.description}\n"
        f"💰 **Recompensa:** `{mission.points_reward}` puntos\n"
        f"⏰ **Tipo:** `{mission.type.capitalize()}`"
    )

async def get_reward_details_message(reward: Reward) -> str:
    stock_info = f"En stock: `{reward.stock}` unidades" if reward.stock != -1 else "Stock: Ilimitado"
    return (
        f"🛍️ **Recompensa: {reward.name}**\n\n"
        f"📝 **Descripción:** {reward.description}\n"
        f"💰 **Costo:** `{reward.cost}` puntos\n"
        f"📦 {stock_info}"
    )
