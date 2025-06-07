# handlers/user_handlers.py
import datetime
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database.models import User, Mission, Reward
from services.point_service import PointService
from services.level_service import LevelService, get_level_threshold
from services.achievement_service import AchievementService, ACHIEVEMENTS
from services.mission_service import MissionService
from services.reward_service import RewardService
from utils.keyboard_utils import (
    get_main_menu_keyboard, get_profile_keyboard, get_missions_keyboard,
    get_reward_keyboard, get_confirm_purchase_keyboard, get_ranking_keyboard
)
from utils.message_utils import get_profile_message, get_mission_details_message, get_reward_details_message
from config import Config
import asyncio

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession):
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name # Mantener para la creación de usuario, pero no usar en mensajes públicos
    last_name = message.from_user.last_name

    user = await session.get(User, user_id)
    if not user:
        user = User(id=user_id, username=username, first_name=first_name, last_name=last_name)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        # Mensaje de bienvenida inicial (se puede personalizar más adelante)
        welcome_text = (
            f"🎉 ¡Bienvenido{' de nuevo' if user.username else ''} a la comunidad VIP! 🎉\n\n"
            "Aquí podrás acumular puntos, subir de nivel, desbloquear logros y canjear recompensas exclusivas "
            "interactuando con el contenido del canal. ¡Tu anonimato es importante para nosotros!\n\n"
            "Usa el menú de abajo para explorar tus opciones."
        )
    else:
        # Mensaje para usuarios existentes
        welcome_text = (
            f"👋 ¡Hola{' de nuevo' if user.username else ''}! ¿Listo para seguir explorando la exclusividad?\n\n"
            "Usa el menú de abajo para ver tus puntos, misiones y recompensas."
        )

    await message.answer(welcome_text, reply_markup=get_main_menu_keyboard(), parse_mode="Markdown")


@router.message(F.text == "👤 Mi Perfil")
@router.message(Command("mispuntos"))
async def show_profile(message: Message, session: AsyncSession):
    user = await session.get(User, message.from_user.id)
    if not user:
        await message.answer("Parece que no estás registrado. Por favor, usa /start para iniciar.")
        return

    mission_service = MissionService(session)
    active_missions = await mission_service.get_active_missions(user.id)

    # get_profile_message ya se encarga de formatear el texto
    profile_text = await get_profile_message(user, active_missions)
    await message.answer(profile_text, reply_markup=get_profile_keyboard(), parse_mode="Markdown")


@router.callback_query(F.data == "profile_achievements")
async def show_achievements(callback: CallbackQuery, session: AsyncSession):
    user = await session.get(User, callback.from_user.id)
    if not user:
        await callback.answer("Usuario no encontrado.", show_alert=True)
        return

    achievement_service = AchievementService(session)
    granted_achievements_data = await achievement_service.get_user_achievements(user.id)

    if not granted_achievements_data:
        achievements_text = "No tienes logros aún. ¡Sigue interactuando para desbloquearlos! 🚀"
    else:
        # Order achievements by granted_at (most recent first)
        sorted_achievements = sorted(
            granted_achievements_data.values(),
            key=lambda x: datetime.datetime.fromisoformat(x['granted_at']),
            reverse=True
        )
        achievements_formatted = [f"{ach['icon']} `{ach['name']}` - Desbloqueado el `{datetime.datetime.fromisoformat(ach['granted_at']).strftime('%d/%m/%Y')}`" for ach in sorted_achievements]
        achievements_text = "🏆 **Tus Logros Desbloqueados:**\n\n" + "\n".join(achievements_formatted)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Volver al Perfil", callback_data="show_profile")] # Volver al perfil
    ])
    await callback.message.edit_text(achievements_text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer() # Close the loading animation on the button


@router.callback_query(F.data == "show_profile") # Handler para el botón "Volver al Perfil"
async def back_to_profile(callback: CallbackQuery, session: AsyncSession):
    user = await session.get(User, callback.from_user.id)
    if not user:
        await callback.answer("Usuario no encontrado.", show_alert=True)
        return
    mission_service = MissionService(session)
    active_missions = await mission_service.get_active_missions(user.id)
    profile_text = await get_profile_message(user, active_missions)
    await callback.message.edit_text(profile_text, reply_markup=get_profile_keyboard(), parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data == "profile_missions_active")
async def show_active_missions_profile(callback: CallbackQuery, session: AsyncSession):
    user = await session.get(User, callback.from_user.id)
    if not user:
        await callback.answer("Usuario no encontrado.", show_alert=True)
        return

    mission_service = MissionService(session)
    active_missions = await mission_service.get_active_missions(user.id)

    if not active_missions:
        missions_text = "No tienes misiones activas. ¡Revisa la sección 'Misiones' para nuevas oportunidades! 🎯"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Volver al Perfil", callback_data="show_profile")]
        ])
    else:
        missions_list_text = []
        for mission in active_missions:
            missions_list_text.append(f"- **{mission.name}** (`{mission.points_reward}` Pts)")
        missions_text = "🎯 **Tus Misiones Activas:**\n\n" + "\n".join(missions_list_text)

        # Aquí podríamos querer mostrar un botón para ir a la sección completa de misiones si es muy larga
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Ver todas las misiones", callback_data="show_missions")], # Podría llevar al /missions
            [InlineKeyboardButton(text="🔙 Volver al Perfil", callback_data="show_profile")]
        ])

    await callback.message.edit_text(missions_text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()


@router.message(F.text == "🎯 Misiones")
@router.message(Command("misiones"))
async def show_missions(message: Message, session: AsyncSession):
    user = await session.get(User, message.from_user.id)
    if not user:
        await message.answer("Parece que no estás registrado. Por favor, usa /start para iniciar.")
        return

    mission_service = MissionService(session)
    missions = await mission_service.get_active_missions(user.id) # Get all active missions, filtered by user completion

    if not missions:
        await message.answer("No hay misiones activas disponibles en este momento. ¡Vuelve pronto!", reply_markup=get_missions_keyboard([]), parse_mode="Markdown")
        return

    # Using get_missions_keyboard with offset
    await message.answer("🎯 **Misiones disponibles:**", reply_markup=get_missions_keyboard(missions, 0), parse_mode="Markdown")


@router.callback_query(F.data.startswith("missions_nav_"))
async def navigate_missions(callback: CallbackQuery, session: AsyncSession):
    offset = int(callback.data.split("_")[2])
    user = await session.get(User, callback.from_user.id)
    if not user:
        await callback.answer("Usuario no encontrado.", show_alert=True)
        return

    mission_service = MissionService(session)
    missions = await mission_service.get_active_missions(user.id)

    if not missions:
        await callback.message.edit_text("No hay misiones activas disponibles en este momento. ¡Vuelve pronto!", reply_markup=get_missions_keyboard([]), parse_mode="Markdown")
        await callback.answer()
        return

    await callback.message.edit_text("🎯 **Misiones disponibles:**", reply_markup=get_missions_keyboard(missions, offset), parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data.startswith("mission_"))
async def show_mission_details(callback: CallbackQuery, session: AsyncSession):
    mission_id = callback.data.split("_")[1]
    mission_service = MissionService(session)
    mission = await mission_service.get_mission_by_id(mission_id)

    if not mission:
        await callback.answer("Misión no encontrada o inactiva.", show_alert=True)
        return

    # Check if user already completed this mission for the current period
    user = await session.get(User, callback.from_user.id)
    if not user:
        await callback.answer("Usuario no encontrado.", show_alert=True)
        return

    # Re-check completion logic if needed, as get_active_missions already filters
    # For now, assume if we got here, it's active and not completed for the period
    # But a direct check is safer if this handler can be reached independently
    is_completed_for_period, _ = await mission_service.check_mission_completion_status(user, mission)
    if is_completed_for_period:
        await callback.answer("Ya completaste esta misión. ¡Vuelve cuando se reinicie!", show_alert=True)
        return

    mission_text = await get_mission_details_message(mission)
    complete_button = []
    # If mission requires a specific action outside the bot's menu, don't show a complete button here.
    # We will need specific handlers for those actions.
    if not mission.requires_action:
        complete_button.append([InlineKeyboardButton(text="✅ Completar Misión", callback_data=f"complete_mission_{mission_id}")])

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        *complete_button,
        [InlineKeyboardButton(text="🔙 Volver a Misiones", callback_data=f"show_missions")] # Volver a la lista de misiones
    ])
    await callback.message.edit_text(mission_text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data.startswith("complete_mission_"))
async def complete_mission(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    mission_id = callback.data.split("_")[2]
    user_id = callback.from_user.id

    mission_service = MissionService(session)
    point_service = PointService(session)
    level_service = LevelService(session)
    achievement_service = AchievementService(session)

    success, mission = await mission_service.complete_mission(user_id, mission_id)

    if success:
        user = await session.get(User, user_id) # Get updated user
        await point_service.add_points(user_id, mission.points_reward)
        leveled_up = await level_service.check_for_level_up(user)

        response_text = f"✅ ¡Misión '{mission.name}' completada! Has ganado `{mission.points_reward}` puntos."
        if leveled_up:
            response_text += f" ¡Felicidades, has subido al Nivel {user.level}!"

        # Check for achievements based on mission completion (example)
        if mission_id == "first_mission_example_id": # Replace with actual first mission ID
            if await achievement_service.grant_achievement(user_id, "first_mission"):
                response_text += f"\n🏆 ¡Has desbloqueado el logro 'Primera Misión Completada'!"

        await callback.message.edit_text(response_text, reply_markup=get_profile_keyboard(), parse_mode="Markdown") # Redirigir al perfil
    else:
        response_text = "❌ No pudimos completar la misión. Asegúrate de que sea una misión activa o que no la hayas completado ya para este periodo."
        await callback.answer(response_text, show_alert=True)

    await callback.answer()


@router.message(F.text == "🛍️ Tienda de Recompensas")
@router.message(Command("tienda"))
async def show_rewards(message: Message, session: AsyncSession):
    user = await session.get(User, message.from_user.id)
    if not user:
        await message.answer("Parece que no estás registrado. Por favor, usa /start para iniciar.")
        return

    reward_service = RewardService(session)
    rewards = await reward_service.get_active_rewards()

    if not rewards:
        await message.answer("La tienda de recompensas está vacía. ¡Vuelve pronto!", reply_markup=get_reward_keyboard([]), parse_mode="Markdown")
        return

    await message.answer("🛍️ **Recompensas disponibles:**", reply_markup=get_reward_keyboard(rewards, 0), parse_mode="Markdown")


@router.callback_query(F.data.startswith("rewards_nav_"))
async def navigate_rewards(callback: CallbackQuery, session: AsyncSession):
    offset = int(callback.data.split("_")[2])
    reward_service = RewardService(session)
    rewards = await reward_service.get_active_rewards()

    if not rewards:
        await callback.message.edit_text("La tienda de recompensas está vacía. ¡Vuelve pronto!", reply_markup=get_reward_keyboard([]), parse_mode="Markdown")
        await callback.answer()
        return

    await callback.message.edit_text("🛍️ **Recompensas disponibles:**", reply_markup=get_reward_keyboard(rewards, offset), parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data.startswith("reward_"))
async def show_reward_details(callback: CallbackQuery, session: AsyncSession):
    reward_id = int(callback.data.split("_")[1])
    reward_service = RewardService(session)
    reward = await reward_service.get_reward_by_id(reward_id)

    if not reward or not reward.is_active:
        await callback.answer("Recompensa no encontrada o no disponible.", show_alert=True)
        return

    user = await session.get(User, callback.from_user.id)
    if not user:
        await callback.answer("Usuario no encontrado.", show_alert=True)
        return

    reward_text = await get_reward_details_message(reward, user.points)
    await callback.message.edit_text(reward_text, reply_markup=get_confirm_purchase_keyboard(reward_id), parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data.startswith("purchase_"))
async def confirm_purchase(callback: CallbackQuery, session: AsyncSession):
    reward_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id

    reward_service = RewardService(session)
    success, message = await reward_service.purchase_reward(user_id, reward_id)

    if success:
        await callback.message.edit_text(message, reply_markup=get_main_menu_keyboard(), parse_mode="Markdown") # Volver al menú principal
    else:
        await callback.message.edit_text(message, reply_markup=get_confirm_purchase_keyboard(reward_id), parse_mode="Markdown") # Mostrar el mensaje de error y mantener opciones de recompensa
    await callback.answer()


@router.message(F.text == "🏆 Ranking")
@router.message(Command("ranking"))
async def show_ranking(message: Message, session: AsyncSession):
    user_id = message.from_user.id # Get current user's ID
    offset = 0 # Start from the beginning

    stmt = select(User).order_by(User.points.desc()).offset(offset).limit(10)
    result = await session.execute(stmt)
    top_users = result.scalars().all()

    total_users_stmt = select(func.count(User.id))
    total_users_result = await session.execute(total_users_stmt)
    total_users = total_users_result.scalar_one()

    if not top_users:
        await message.answer("Aún no hay usuarios en el ranking. ¡Sé el primero en la cima! 🚀", reply_markup=get_ranking_keyboard(), parse_mode="Markdown")
        return

    ranking_text = "🏆 **Ranking de Usuarios (Top 10):**\n\n"
    for i, user in enumerate(top_users):
        # ANOMINIZACIÓN DEL RANKING
        display_name = ""
        if user.id == user_id: # Si es el usuario actual, mostrar su nombre completo (o username si no tiene name)
            display_name = user.first_name or user.username or "Tú"
        else: # Para otros usuarios, anonimizar
            if user.username:
                display_name = f"@{user.username[0]}*****" # Primera letra del username y asteriscos
            elif user.first_name:
                display_name = f"{user.first_name[0]}*****" # Primera letra del first_name y asteriscos
            else:
                display_name = "Usuario Anónimo" # Fallback si no hay nombre ni username

        ranking_text += f"`{offset + i + 1}.` {display_name} - `{user.points}` puntos (Nivel `{user.level}`)\n"

    await message.answer(ranking_text, reply_markup=get_ranking_keyboard(offset, total_users), parse_mode="Markdown")

@router.callback_query(F.data.startswith("ranking_nav_"))
async def navigate_ranking(callback: CallbackQuery, session: AsyncSession):
    user_id = callback.from_user.id # Get current user's ID
    offset = int(callback.data.split("_")[2])
    stmt = select(User).order_by(User.points.desc()).offset(offset).limit(10)
    result = await session.execute(stmt)
    top_users = result.scalars().all()

    total_users_stmt = select(func.count(User.id))
    total_users_result = await session.execute(total_users_stmt)
    total_users = total_users_result.scalar_one()

    if not top_users:
        await callback.message.edit_text("Aún no hay usuarios en el ranking. ¡Sé el primero en la cima! 🚀", reply_markup=get_ranking_keyboard(), parse_mode="Markdown")
        await callback.answer()
        return

    ranking_text = "🏆 **Ranking de Usuarios:**\n\n"
    for i, user in enumerate(top_users):
        # ANOMINIZACIÓN DEL RANKING
        display_name = ""
        if user.id == user_id: # Si es el usuario actual, mostrar su nombre completo (o username si no tiene name)
            display_name = user.first_name or user.username or "Tú"
        else: # Para otros usuarios, anonimizar
            if user.username:
                display_name = f"@{user.username[0]}*****" # Primera letra del username y asteriscos
            elif user.first_name:
                display_name = f"{user.first_name[0]}*****" # Primera letra del first_name y asteriscos
            else:
                display_name = "Usuario Anónimo" # Fallback si no hay nombre ni username

        ranking_text += f"`{offset + i + 1}.` {display_name} - `{user.points}` puntos (Nivel `{user.level}`)\n"

    await callback.message.edit_text(ranking_text, reply_markup=get_ranking_keyboard(offset, total_users), parse_mode="Markdown")
    await callback.answer()

# --- NUEVO HANDLER PARA "VOLVER AL MENÚ PRINCIPAL" ---
@router.callback_query(F.data == "main_menu")
async def back_to_main_menu(callback: CallbackQuery, session: AsyncSession):
    user_id = callback.from_user.id
    user = await session.get(User, user_id)
    if not user:
        await callback.answer("Usuario no encontrado. Por favor, usa /start.", show_alert=True)
        return

    # Mensaje genérico para el menú principal, anonimizado
    menu_message = "¡Bienvenido de nuevo! Aquí puedes navegar por las opciones principales de la comunidad VIP."
    await callback.message.edit_text(menu_message, reply_markup=get_main_menu_keyboard(), parse_mode="Markdown")
    await callback.answer()

