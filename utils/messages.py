from database.models import User, Mission, Reward
from services.level_service import LEVELS, get_level_by_points, get_progress_to_next_level
from services.achievement_service import ACHIEVEMENTS
from utils.messages import BOT_MESSAGES

async def get_profile_message(user: User, active_missions: list[Mission]) -> str:
    progress = get_progress_to_next_level(user.points)
    if progress["next_level"]:
        points_to_next_level_text = BOT_MESSAGES["profile_points_to_next_level"].format(
            points_needed=progress["points_to_next"],
            next_level=progress["next_level"],
            next_level_threshold=(
                next(
                    (lvl["min_points"] for lvl in LEVELS if lvl["name"] == progress["next_level"]),
                    "?"
                )
            )
        )
    else:
        points_to_next_level_text = BOT_MESSAGES["profile_max_level"]

    achievements_text = BOT_MESSAGES["profile_no_achievements"]
    if user.achievements:
        granted_achievements_list = []
        for ach_id, timestamp_str in user.achievements.items():
            if ach_id in ACHIEVEMENTS:
                granted_achievements_list.append({
                    "id": ach_id,
                    "name": ACHIEVEMENTS[ach_id]["name"],
                    "emoji": ACHIEVEMENTS[ach_id].get("emoji", ""),
                    "date": timestamp_str
                })
        if granted_achievements_list:
            achievements_lines = [
                f"{a['emoji']} {a['name']} ({a['date']})"
                for a in granted_achievements_list
            ]
            achievements_text = "\n".join(achievements_lines)

    missions_text = ""
    if active_missions:
        missions_text = "\n".join([f"• {m.name}: {m.description}" for m in active_missions])

    return (
        f"👤 *Perfil de usuario*\n"
        f"Nivel: {progress['current_level']}\n"
        f"Puntos: {progress['current_points']}\n"
        f"{points_to_next_level_text}\n"
        f"🏆 Logros:\n{achievements_text}\n"
        f"🔥 Misiones activas:\n{missions_text}\n"
    )

async def send_progress_bar(message, percent):
    # Ejemplo simple de barra de progreso textual
    total_slots = 20
    filled_slots = int(percent / 100 * total_slots)
    bar = "█" * filled_slots + "░" * (total_slots - filled_slots)
    await message.answer(f"Progreso: [{bar}] {percent}%")

async def send_achievements_gallery(message, session, user: User):
    # Simula galería de logros (puedes expandir visualmente)
    achievements = user.achievements or {}
    if not achievements:
        await message.answer("Aún no has desbloqueado logros.")
        return
    lines = []
    for ach_id, timestamp_str in achievements.items():
        if ach_id in ACHIEVEMENTS:
            ach = ACHIEVEMENTS[ach_id]
            lines.append(f"{ach.get('emoji','')} {ach['name']} — {timestamp_str}")
    await message.answer("🏆 *Logros desbloqueados:*\n" + "\n".join(lines), parse_mode="Markdown")
