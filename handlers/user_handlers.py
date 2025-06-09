import datetime
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database.models import User, Mission, Reward, get_user_menu_state, set_user_menu_state
from services.point_service import PointService
from services.level_service import LevelService
from services.achievement_service import AchievementService, ACHIEVEMENTS
from services.mission_service import MissionService
from services.reward_service import RewardService
from utils.keyboard_utils import (
    get_main_menu_keyboard, get_profile_keyboard, get_missions_keyboard,
    get_reward_keyboard, get_confirm_purchase_keyboard, get_ranking_keyboard,
    get_reaction_keyboard,
    get_root_menu, get_parent_menu, get_child_menu
)

router = Router()

@router.callback_query(F.data.startswith("menu:"))
async def menu_callback_handler(callback: CallbackQuery, session: AsyncSession):
    user_id = callback.from_user.id
    current_menu = callback.data.split(":")[1]

    if current_menu == "back":
        parent_menu = await get_user_menu_state(session, user_id)

        if parent_menu == "root":
            await callback.message.edit_reply_markup(reply_markup=get_root_menu())
            return

        if parent_menu:
            await callback.message.edit_reply_markup(reply_markup=get_parent_menu(parent_menu))
            await set_user_menu_state(session, user_id, "root")
        else:
            await callback.message.edit_reply_markup(reply_markup=get_root_menu())
            await set_user_menu_state(session, user_id, "root")
    else:
        await set_user_menu_state(session, user_id, current_menu)
        await callback.message.edit_reply_markup(reply_markup=get_child_menu(current_menu))

@router.message(CommandStart())
async def handle_start(message: Message, session: AsyncSession):
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name

    user = await session.get(User, user_id)
    if not user:
        user = User(id=user_id, username=username, first_name=first_name, last_name=last_name)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        logger.info(f"Nuevo usuario registrado: {user_id} ({username})")
        await message.answer(
            f"¡Hola, {first_name}! 👋\n"
            "¡Bienvenido al sistema de gamificación! Conmigo, podrás ganar puntos por participar, completar misiones y desbloquear logros.\n\n"
            "Usa el menú de abajo para navegar:",
            reply_markup=get_main_menu_keyboard()
        )
    else:
        await message.answer(
            f"¡Bienvenido de nuevo, {first_name}! 🎉\n"
            "Aquí está tu menú principal:",
            reply_markup=get_main_menu_keyboard()
        )

@router.callback_query(F.data == "main_menu")
async def back_to_main_menu(callback: CallbackQuery):
    await callback.message.edit_text("Aquí está tu menú principal:", reply_markup=get_main_menu_keyboard())
    await callback.answer()

@router.message(F.text == "👤 Mi Perfil")
async def show_profile(message: Message, session: AsyncSession):
    user = await session.get(User, message.from_user.id)
    if not user:
        await message.answer("Usuario no encontrado. Por favor, usa /start.")
        return

    mission_service = MissionService(session)
    active_missions = await mission_service.get_active_missions(message.from_user.id)

    profile_message = await get_profile_message(user, active_missions)
    await message.answer(profile_message, parse_mode="Markdown", reply_markup=get_profile_keyboard())

@router.callback_query(F.data == "profile_achievements")
async def show_achievements(callback: CallbackQuery, session: AsyncSession):
    user = await session.get(User, callback.from_user.id)
    if not user:
        await callback.answer("Usuario no encontrado.", show_alert=True)
        return

    achievement_service = AchievementService(session)
    user_achievements = await achievement_service.get_user_achievements(user.id)

    if not user_achievements:
        achievements_text = "No tienes logros aún. ¡Sigue interactuando para desbloquearlos! 🚀"
    else:
        granted_achievements_list = []
        for ach_id, ach_data in user_achievements.items(): # user_achievements is now dict with data
            if ach_id in ACHIEVEMENTS:
                granted_achievements_list.append({
                    "id": ach_id,
                    "name": ach_data['name'], # Use name from ach_data if available
                    "icon": ach_data['icon'], # Use icon from ach_data if available
                    "granted_at": ach_data['granted_at'] # Use granted_at from ach_data
                })
        # Sort by granted_at (most recent first)
        granted_achievements_list.sort(key=lambda x: x['granted_at'], reverse=True)

        achievements_formatted = [f"{ach['icon']} `{ach['name']}` (Desbloqueado el: `{datetime.datetime.fromisoformat(ach['granted_at']).strftime('%d/%m/%Y')}`)" for ach in granted_achievements_list]
        achievements_text = "🏆 **Tus Logros Desbloqueados:**\n\n" + "\n".join(achievements_formatted)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Volver al Perfil", callback_data="show_profile_menu")]
    ])
    await callback.message.edit_text(achievements_text, parse_mode="Markdown", reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data == "show_profile_menu") # Callback para volver al perfil desde logros
async def back_to_profile_menu(callback: CallbackQuery, session: AsyncSession):
    user = await session.get(User, callback.from_user.id)
    if not user:
        await callback.answer("Usuario no encontrado.", show_alert=True)
        return

    mission_service = MissionService(session)
    active_missions = await mission_service.get_active_missions(callback.from_user.id)
    profile_message = await get_profile_message(user, active_missions)
    await callback.message.edit_text(profile_message, parse_mode="Markdown", reply_markup=get_profile_keyboard())
    await callback.answer()


@router.message(F.text == "🎯 Misiones")
@router.callback_query(F.data == "profile_missions_active") # Usar este callback para mostrar misiones activas desde el perfil
@router.callback_query(F.data.startswith("missions_nav_")) # Callback para navegación de misiones
async def show_missions(callback_or_message: Message | CallbackQuery, session: AsyncSession):
    user_id = callback_or_message.from_user.id
    offset = 0
    if isinstance(callback_or_message, CallbackQuery) and callback_or_message.data.startswith("missions_nav_"):
        offset = int(callback_or_message.data.split("_")[2])

    mission_service = MissionService(session)
    active_missions = await mission_service.get_active_missions(user_id)

    if not active_missions:
        text = "No tienes misiones activas en este momento. ¡Sigue revisando para nuevas oportunidades! 🚀"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Volver al Menú Principal", callback_data="main_menu")]
        ])
        if isinstance(callback_or_message, CallbackQuery):
            await callback_or_message.message.edit_text(text, reply_markup=keyboard)
            await callback_or_message.answer()
        else:
            await callback_or_message.answer(text, reply_markup=keyboard)
        return

    missions_on_page = active_missions[offset:offset+5]
    keyboard = get_missions_keyboard(active_missions, offset)

    mission_list_text = "🎯 **Tus Misiones Activas:**\n\n"
    for mission in missions_on_page:
        mission_list_text += f"▪️ **{mission.name}** (`{mission.points_reward}` Pts)\n"
        mission_list_text += f"   _Tipo: {mission.type.capitalize()}_ - {mission.description}\n\n"

    if isinstance(callback_or_message, CallbackQuery):
        await callback_or_message.message.edit_text(mission_list_text, parse_mode="Markdown", reply_markup=keyboard)
        await callback_or_message.answer()
    else:
        await callback_or_message.answer(mission_list_text, parse_mode="Markdown", reply_markup=keyboard)


@router.callback_query(F.data.startswith("mission_"))
async def show_mission_details(callback: CallbackQuery, session: AsyncSession):
    mission_id = callback.data.split("_")[1]
    mission_service = MissionService(session)
    mission = await session.get(Mission, mission_id)

    if not mission:
        await callback.answer("Misión no encontrada.", show_alert=True)
        return

    details_message = await get_mission_details_message(mission)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Completar Misión (Manual)", callback_data=f"complete_mission_{mission_id}")],
        [InlineKeyboardButton(text="🔙 Volver a Misiones", callback_data="missions_nav_0")] # Volver a la primera página de misiones
    ])
    await callback.message.edit_text(details_message, parse_mode="Markdown", reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data.startswith("complete_mission_"))
async def complete_mission(callback: CallbackQuery, session: AsyncSession):
    mission_id = callback.data.split("_")[1]
    user_id = callback.from_user.id

    mission_service = MissionService(session)
    point_service = PointService(session)
    level_service = LevelService(session)
    achievement_service = AchievementService(session)

    # Check if mission requires action
    mission = await session.get(Mission, mission_id)
    if mission and mission.requires_action and mission.type != 'reaction': # Reaction missions are completed via handle_channel_reaction
        await callback.answer("Esta misión requiere una acción específica fuera del bot para completarse.", show_alert=True)
        return

    completed, mission_obj = await mission_service.complete_mission(user_id, mission_id)

    if completed:
        updated_user = await point_service.add_points(user_id, mission_obj.points_reward)
        leveled_up = await level_service.check_for_level_up(updated_user)
        await achievement_service.grant_achievement(user_id, "first_mission") # Grant achievement for first mission

        alert_message = f"¡Misión '{mission_obj.name}' completada! Ganaste `{mission_obj.points_reward}` puntos."
        if leveled_up:
            alert_message += f"\n\n✨ ¡Felicidades! Has subido al nivel `{updated_user.level}`."
        
        await callback.answer(alert_message, show_alert=True)
        await show_missions(callback, session) # Refresh missions list
    else:
        await callback.answer("No puedes completar esta misión ahora. Ya está completada o no cumples los requisitos.", show_alert=True)

# handlers/user_handlers.py - Bloque 2 de 2 (continuación)

@router.message(F.text == "🛍️ Tienda de Recompensas")
@router.callback_query(F.data.startswith("rewards_nav_"))
async def show_rewards(callback_or_message: Message | CallbackQuery, session: AsyncSession):
    offset = 0
    if isinstance(callback_or_message, CallbackQuery) and callback_or_message.data.startswith("rewards_nav_"):
        offset = int(callback_or_message.data.split("_")[2])

    reward_service = RewardService(session)
    active_rewards = await reward_service.get_active_rewards()

    if not active_rewards:
        text = "La tienda de recompensas está vacía en este momento. ¡Vuelve más tarde! 🎁"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Volver al Menú Principal", callback_data="main_menu")]
        ])
        if isinstance(callback_or_message, CallbackQuery):
            await callback_or_message.message.edit_text(text, reply_markup=keyboard)
            await callback_or_message.answer()
        else:
            await callback_or_message.answer(text, reply_markup=keyboard)
        return

    rewards_on_page = active_rewards[offset:offset+5]
    keyboard = get_reward_keyboard(active_rewards, offset)

    rewards_list_text = "🛍️ **Tienda de Recompensas:**\n\n"
    for reward in rewards_on_page:
        stock_info = f"({reward.stock} en stock)" if reward.stock != -1 else "(Stock ilimitado)"
        rewards_list_text += f"▪️ **{reward.name}** (`{reward.cost}` Puntos) {stock_info}\n"
        rewards_list_text += f"   _Descripción: {reward.description}_\n\n"

    if isinstance(callback_or_message, CallbackQuery):
        await callback_or_message.message.edit_text(rewards_list_text, parse_mode="Markdown", reply_markup=keyboard)
        await callback_or_message.answer()
    else:
        await callback_or_message.answer(rewards_list_text, parse_mode="Markdown", reply_markup=keyboard)


@router.callback_query(F.data.startswith("reward_"))
async def show_reward_details(callback: CallbackQuery, session: AsyncSession):
    reward_id = int(callback.data.split("_")[1])
    reward_service = RewardService(session)
    reward = await reward_service.get_reward_by_id(reward_id)

    if not reward:
        await callback.answer("Recompensa no encontrada.", show_alert=True)
        return

    details_message = await get_reward_details_message(reward)
    keyboard = get_confirm_purchase_keyboard(reward_id)

    await callback.message.edit_text(details_message, parse_mode="Markdown", reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data.startswith("confirm_purchase_"))
async def confirm_purchase(callback: CallbackQuery, session: AsyncSession):
    reward_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id

    reward_service = RewardService(session)
    achievement_service = AchievementService(session)

    success, message = await reward_service.purchase_reward(user_id, reward_id)

    if success:
        await achievement_service.grant_achievement(user_id, "first_purchase")
        await callback.answer(f"✅ {message}", show_alert=True)
        await show_rewards(callback, session) # Refresh rewards list
    else:
        await callback.answer(f"❌ {message}", show_alert=True)


@router.message(F.text == "🏆 Ranking")
@router.callback_query(F.data.startswith("ranking_nav_"))
async def show_ranking(callback_or_message: Message | CallbackQuery, session: AsyncSession):
    offset = 0
    if isinstance(callback_or_message, CallbackQuery) and callback_or_message.data.startswith("ranking_nav_"):
        offset = int(callback_or_message.data.split("_")[2])

    stmt = select(User).order_by(User.points.desc()).offset(offset).limit(10)
    result = await session.execute(stmt)
    top_users = result.scalars().all()

    total_users_stmt = select(func.count(User.id))
    total_users_result = await session.execute(total_users_stmt)
    total_users = total_users_result.scalar_one()

    if not top_users:
        text = "Aún no hay usuarios en el ranking. ¡Sé el primero en la cima! 🚀"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Volver al Menú Principal", callback_data="main_menu")]
        ])
        if isinstance(callback_or_message, CallbackQuery):
            await callback_or_message.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
            await callback_or_message.answer()
        else:
            await callback_or_message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
        return

    ranking_text = "🏆 **Ranking de Usuarios (Top 10):**\n\n"
    for i, user in enumerate(top_users):
        ranking_text += f"`{offset + i + 1}.` {user.first_name or user.username} - `{user.points}` puntos (Nivel `{user.level}`)\n"

    # Only show pagination buttons if there are more users than currently displayed
    keyboard = get_ranking_keyboard(offset, total_users)

    if isinstance(callback_or_message, CallbackQuery):
        await callback_or_message.message.edit_text(ranking_text, reply_markup=keyboard, parse_mode="Markdown")
        await callback_or_message.answer()
    else:
        await callback_or_message.answer(ranking_text, reply_markup=keyboard, parse_mode="Markdown")


@router.callback_query(F.data.startswith("react_"))
async def handle_channel_reaction(callback: CallbackQuery, session: AsyncSession, state: FSMContext, bot: Bot):
    user_id = callback.from_user.id
    message_id = int(callback.data.split("_")[1]) # Extrae el ID del mensaje
    reaction_type = callback.data.split("_")[2] # Extrae el tipo de reacción (e.g., 'reflect', 'inspire', 'emotion')

    user = await session.get(User, user_id)
    if not user:
        # El usuario no existe, podría ser un buen lugar para registrarlo o pedirle que inicie el bot
        await callback.answer("Por favor, inicia el bot con /start para participar.", show_alert=True)
        return

    # Initialize channel_reactions if it's None
    if user.channel_reactions is None:
        user.channel_reactions = {}

    # Check if the user has already reacted to this specific message
    if str(message_id) in user.channel_reactions and user.channel_reactions[str(message_id)]:
        await callback.answer("Ya has registrado tu reflexión en este post. ¡Gracias!", show_alert=True)
        return

    # Get services
    point_service = PointService(session)
    level_service = LevelService(session)
    achievement_service = AchievementService(session)
    mission_service = MissionService(session) # <-- ¡NUEVA INSTANCIA DE MISSIONSERVICE!

    # Record the reaction in the user's data
    user.channel_reactions[str(message_id)] = reaction_type
    await session.commit()
    await session.refresh(user)

    # --- LÓGICA DE PUNTOS Y RECOMPENSAS POR REACCIÓN ---
    # Puedes definir aquí los puntos por una reacción base, o dejar que solo las misiones los den
    base_points_for_reaction = 10 # Ejemplo: 10 puntos por cada reacción única en un mensaje
    updated_user = await point_service.add_points(user_id, base_points_for_reaction)

    # Check for level up
    leveled_up = await level_service.check_for_level_up(updated_user)

    # Check for first mission achievement (if applicable)
    # Asegúrate de tener este logro definido en ACHIEVEMENTS en achievement_service.py
    await achievement_service.grant_achievement(user_id, "first_reaction") # Si tienes un logro "first_reaction"

    # --- ¡NUEVA LÓGICA PARA COMPLETAR MISIONES DE REACCIÓN! ---
    # Buscar misiones activas de tipo 'reaction'
    active_reaction_missions = await mission_service.get_active_missions(user_id=user_id, mission_type='reaction')

    mission_completed_message = ""
    for mission in active_reaction_missions:
        # Aquí puedes añadir lógica más compleja si la misión requiere un tipo de reacción específico
        # Por ahora, cualquier reacción en un mensaje nuevo completa la misión de reacción.
        # Si quisieras, por ejemplo, que una misión sea "reaccionar con ❤️", la action_data de la misión podría especificarlo.
        
        # Check if the user has already completed this mission for the current period
        is_completed_for_period, _ = await mission_service.check_mission_completion_status(user, mission)
        
        if not is_completed_for_period:
            completed, mission_obj = await mission_service.complete_mission(user_id, mission.id, reaction_type) # Puedes pasar reaction_type como data de acción si lo necesitas
            if completed:
                mission_completed_message = f"\n\n🎉 ¡Misión completada: **{mission_obj.name}**! Ganaste `{mission_obj.points_reward}` puntos adicionales."
                # Asumimos que add_points ya maneja el multiplicador de eventos si hay uno activo
                updated_user = await point_service.add_points(user_id, mission_obj.points_reward)
                leveled_up = await level_service.check_for_level_up(updated_user) or leveled_up # Check level up again after mission points


    # Prepare the alert message
    alert_message = f"¡Reacción registrada! Ganaste `{base_points_for_reaction}` puntos."
    alert_message += mission_completed_message # Add mission completion message if any

    if leveled_up:
        alert_message += f"\n\n✨ ¡Felicidades! Has subido al nivel `{updated_user.level}`."

    await callback.answer(alert_message, show_alert=True)
    logger.info(f"User {user_id} reacted with {reaction_type} to message {message_id}. Points: {updated_user.points}")

