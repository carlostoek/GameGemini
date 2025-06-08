import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton # Import for external actions in channel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database.models import User, Mission, Reward
from services.point_service import PointService
from services.level_service import LevelService
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
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name

    user = await session.get(User, user_id)
    if not user:
        user = User(id=user_id, username=username, first_name=first_name, last_name=last_name)
        session.add(user)
        await session.commit()
        await session.refresh(user)

    await message.answer(
        f"¡Bienvenido/a al sistema de gamificación, {first_name or username}! 👋\n\n"
        "Aquí podrás ganar puntos, subir de nivel, desbloquear logros y canjear recompensas. "
        "Usa el menú de abajo para navegar. ¡A divertirse! 🎉",
        reply_markup=get_main_menu_keyboard(),
        parse_mode="Markdown"
    )

@router.message(F.text == "👤 Mi Perfil")
@router.message(Command("perfil"))
async def show_profile(message: Message, session: AsyncSession):
    user_id = message.from_user.id
    user = await session.get(User, user_id)
    if not user:
        await message.answer("Parece que no estás registrado. Por favor, inicia con /start.")
        return

    mission_service = MissionService(session)
    active_missions = await mission_service.get_active_missions(user_id=user_id) # Pass user_id to filter for completed missions
    profile_message = await get_profile_message(user, active_missions)
    await message.answer(profile_message, reply_markup=get_profile_keyboard(), parse_mode="Markdown")

@router.callback_query(F.data == "profile_achievements")
async def show_profile_achievements(callback: CallbackQuery, session: AsyncSession):
    user_id = callback.from_user.id
    user = await session.get(User, user_id)
    if not user:
        await callback.answer("Error: Usuario no encontrado.", show_alert=True)
        return

    achievement_service = AchievementService(session)
    granted_achievements = await achievement_service.get_user_achievements(user_id)

    if not granted_achievements:
        text = "No tienes logros desbloqueados aún. ¡Sigue participando para ganar algunos! 💪"
    else:
        text = "🏆 **Tus Logros Desbloqueados:**\n\n"
        # Sort achievements by granted_at timestamp (most recent first)
        sorted_achievements = sorted(
            granted_achievements.items(),
            key=lambda item: item[1].get('granted_at', '0000-00-00T00:00:00'), # Default for sorting if missing
            reverse=True
        )
        for ach_id, ach_data in sorted_achievements:
            granted_date = ach_data.get('granted_at', 'N/A')[:10] # Take only date part
            text += f"{ach_data['icon']} `{ach_data['name']}` (desbloqueado el: {granted_date})\n"

    await callback.message.edit_text(text, reply_markup=get_profile_keyboard(), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "profile_missions_active")
async def show_profile_active_missions(callback: CallbackQuery, session: AsyncSession):
    user_id = callback.from_user.id
    user = await session.get(User, user_id)
    if not user:
        await callback.answer("Error: Usuario no encontrado.", show_alert=True)
        return

    mission_service = MissionService(session)
    active_missions = await mission_service.get_active_missions(user_id=user_id)

    if not active_missions:
        text = "No tienes misiones activas por el momento. ¡Vuelve más tarde para nuevas misiones!"
    else:
        text = "🎯 **Tus Misiones Activas:**\n\n"
        for mission in active_missions:
            text += f"- **{mission.name}**\n  _{mission.description}_\n"

    await callback.message.edit_text(text, reply_markup=get_profile_keyboard(), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "main_menu")
async def back_to_main_menu(callback: CallbackQuery, session: AsyncSession):
    user_id = callback.from_user.id
    user = await session.get(User, user_id)
    if not user:
        await callback.answer("Error: Usuario no encontrado.", show_alert=True)
        return
    await callback.message.edit_text(
        f"¡Bienvenido/a al sistema de gamificación, {user.first_name or user.username}! 👋\n\n"
        "Usa el menú de abajo para navegar. ¡A divertirse! 🎉",
        reply_markup=get_main_menu_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.message(F.text == "🎯 Misiones")
async def show_missions(message: Message, session: AsyncSession):
    mission_service = MissionService(session)
    # Ensure missions shown are those available to the specific user, considering resets
    active_missions = await mission_service.get_active_missions(user_id=message.from_user.id)
    if not active_missions:
        await message.answer("Actualmente no hay misiones activas. ¡Vuelve más tarde para nuevas oportunidades!", reply_markup=get_missions_keyboard([]), parse_mode="Markdown")
        return
    text = "🎯 **Misiones Activas:**\n\nSelecciona una misión para ver los detalles y completarla:"
    await message.answer(text, reply_markup=get_missions_keyboard(active_missions), parse_mode="Markdown")

@router.callback_query(F.data.startswith("missions_nav_"))
async def navigate_missions(callback: CallbackQuery, session: AsyncSession):
    offset = int(callback.data.split("_")[2])
    mission_service = MissionService(session)
    active_missions = await mission_service.get_active_missions(user_id=callback.from_user.id)
    if not active_missions:
        await callback.message.edit_text("Actualmente no hay misiones activas. ¡Vuelve más tarde para nuevas oportunidades!", reply_markup=get_missions_keyboard([]), parse_mode="Markdown")
        return
    text = "🎯 **Misiones Activas:**\n\nSelecciona una misión para ver los detalles y completarla:"
    await callback.message.edit_text(text, reply_markup=get_missions_keyboard(active_missions, offset), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data.startswith("mission_"))
async def handle_mission_click(callback: CallbackQuery, session: AsyncSession, bot):
    mission_id = callback.data.split("_")[1]
    user_id = callback.from_user.id
    point_service = PointService(session)
    level_service = LevelService(session)
    achievement_service = AchievementService(session)
    mission_service = MissionService(session)

    mission = await session.get(Mission, mission_id)
    if not mission:
        await callback.answer("Misión no encontrada.", show_alert=True)
        return

    # If the mission requires an external action (e.g., click in a channel post),
    # we don't complete it here. Instead, we instruct the user.
    if mission.requires_action:
        if mission.action_data and mission.action_data.get('button_id'):
            # This is a placeholder. In a real scenario, you'd have posted
            # a message in the channel with this specific callback_data.
            await callback.answer(f"Esta misión requiere que hagas clic en el botón de un post específico en el canal. ¡Mantente atento!", show_alert=True)
            # Example of how you might send a mission post to the channel:
            # await bot.send_message(
            #     Config.CHANNEL_ID,
            #     f"📢 **¡Nueva Misión: {mission.name}!**\n\n{mission.description}\n\n"
            #     f"Haz clic en el botón de abajo para completar y ganar {mission.points_reward} puntos.",
            #     reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            #         [InlineKeyboardButton(text="Completa la Misión", callback_data=f"complete_action_mission_{mission.id}_{mission.action_data['button_id']}")]
            #     ]),
            #     parse_mode="Markdown"
            # )
            return

    # If the mission does not require an external action or action is handled elsewhere
    completed, completed_mission = await mission_service.complete_mission(user_id, mission_id)

    if completed:
        user = await point_service.add_points(user_id, completed_mission.points_reward)
        await callback.answer(f"🎉 ¡Has completado '{completed_mission.name}' y ganado {completed_mission.points_reward} puntos!", show_alert=True)

        # Check for level up
        leveled_up = await level_service.check_for_level_up(user)
        if leveled_up:
            await callback.message.answer(
                f"🌟 ¡Felicidades, {user.first_name or user.username}! ¡Has subido al Nivel {user.level}! ¡Sigue así! 💪",
                parse_mode="Markdown"
            )
            # Check for level achievements
            if user.level >= 5 and await achievement_service.grant_achievement(user_id, "level_5"):
                await callback.message.answer("🏆 ¡Logro desbloqueado: 'Maestro Principiante'!")

        # Check for 'first_mission' achievement
        if await achievement_service.grant_achievement(user_id, "first_mission"):
            await callback.message.answer("🏅 ¡Logro desbloqueado: 'Primera Misión Completada'!")

        # Refresh missions list after completing one
        active_missions = await mission_service.get_active_missions(user_id=user_id)
        text = "🎯 **Misiones Activas:**\n\nSelecciona una misión para ver los detalles y completarla:"
        await callback.message.edit_text(text, reply_markup=get_missions_keyboard(active_missions), parse_mode="Markdown")

    else:
        # Check if it was already completed (and not reset for daily/weekly)
        user = await session.get(User, user_id)
        if mission.id in user.missions_completed:
             await callback.answer(f"Ya has completado la misión '{mission.name}' para el período actual. ¡Vuelve más tarde para la siguiente!", show_alert=True)
        else:
             await callback.answer(f"No puedes completar '{mission.name}' en este momento.", show_alert=True)

# Handler for external action missions (e.g., from a channel post)
@router.callback_query(F.data.startswith("complete_action_mission_"))
async def complete_action_mission(callback: CallbackQuery, session: AsyncSession, bot):
    # This handler would be triggered by a button in a channel post
    parts = callback.data.split("_")
    mission_id = parts[3]
    # action_button_id = parts[4] # If you need to verify the specific button

    user_id = callback.from_user.id
    point_service = PointService(session)
    level_service = LevelService(session)
    achievement_service = AchievementService(session)
    mission_service = MissionService(session)

    mission = await session.get(Mission, mission_id)

    if not mission or not mission.is_active or not mission.requires_action:
        await callback.answer("Esta misión no es válida o no está activa.", show_alert=True)
        return

    # Optional: Verify if the action_button_id matches expected
    # if mission.action_data and mission.action_data.get('button_id') != action_button_id:
    #     await callback.answer("Acción inválida para esta misión.", show_alert=True)
    #     return

    completed, completed_mission = await mission_service.complete_mission(user_id, mission_id)

    if completed:
        user = await point_service.add_points(user_id, completed_mission.points_reward)
        await callback.answer(f"🎉 ¡Misión '{completed_mission.name}' completada! Has ganado {completed_mission.points_reward} puntos. ¡Revisa tu perfil!", show_alert=True)

        leveled_up = await level_service.check_for_level_up(user)
        if leveled_up:
            await bot.send_message(
                user_id,
                f"🌟 ¡Felicidades, {user.first_name or user.username}! ¡Has subido al Nivel {user.level}! ¡Sigue así! 💪",
                parse_mode="Markdown"
            )
            if user.level >= 5 and await achievement_service.grant_achievement(user_id, "level_5"):
                await bot.send_message(user_id, "🏆 ¡Logro desbloqueado: 'Maestro Principiante'!")

        if await achievement_service.grant_achievement(user_id, "first_mission"):
            await bot.send_message(user_id, "🏅 ¡Logro desbloqueado: 'Primera Misión Completada'!")

    else:
        user = await session.get(User, user_id)
        if mission.id in user.missions_completed:
            await callback.answer(f"Ya has completado la misión '{mission.name}' para el período actual. ¡Vuelve más tarde para la siguiente!", show_alert=True)
        else:
            await callback.answer(f"No puedes completar '{mission.name}' en este momento.", show_alert=True)


@router.message(F.text == "🛍️ Tienda de Recompensas")
async def show_store(message: Message, session: AsyncSession):
    reward_service = RewardService(session)
    active_rewards = await reward_service.get_active_rewards()
    if not active_rewards:
        await message.answer("La tienda de recompensas está vacía por el momento. ¡Vuelve más tarde!", reply_markup=get_reward_keyboard([]), parse_mode="Markdown")
        return
    text = "🛍️ **Tienda de Recompensas:**\n\nCanjea tus puntos por increíbles premios. ¡Elige sabiamente! ✨"
    await message.answer(text, reply_markup=get_reward_keyboard(active_rewards), parse_mode="Markdown")

@router.callback_query(F.data.startswith("rewards_nav_"))
async def navigate_rewards(callback: CallbackQuery, session: AsyncSession):
    offset = int(callback.data.split("_")[2])
    reward_service = RewardService(session)
    active_rewards = await reward_service.get_active_rewards()
    if not active_rewards:
        await callback.message.edit_text("La tienda de recompensas está vacía por el momento. ¡Vuelve más tarde!", reply_markup=get_reward_keyboard([]), parse_mode="Markdown")
        return
    text = "🛍️ **Tienda de Recompensas:**\n\nCanjea tus puntos por increíbles premios. ¡Elige sabiamente! ✨"
    await callback.message.edit_text(text, reply_markup=get_reward_keyboard(active_rewards, offset), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data.startswith("reward_"))
async def show_reward_details(callback: CallbackQuery, session: AsyncSession):
    reward_id = int(callback.data.split("_")[1])
    reward_service = RewardService(session)
    reward = await reward_service.get_reward_by_id(reward_id)
    if not reward:
        await callback.answer("Recompensa no encontrada.", show_alert=True)
        return
    text = await get_reward_details_message(reward)
    await callback.message.edit_text(text, reply_markup=get_confirm_purchase_keyboard(reward_id), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data.startswith("confirm_purchase_"))
async def confirm_purchase(callback: CallbackQuery, session: AsyncSession):
    reward_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    reward_service = RewardService(session)
    achievement_service = AchievementService(session) # To check for first purchase achievement

    success, message = await reward_service.purchase_reward(user_id, reward_id)
    await callback.answer(message, show_alert=True)

    if success:
        reward = await reward_service.get_reward_by_id(reward_id)
        user = await session.get(User, user_id) # Refresh user points
        await callback.message.edit_text(
            f"✅ ¡Compra exitosa! Has canjeado `{reward.name}`. 🎉\n"
            f"Tus puntos restantes: `{user.points}`",
            reply_markup=get_main_menu_keyboard(), # Optionally return to main menu or store
            parse_mode="Markdown"
        )
        # Check for achievements related to purchases
        if await achievement_service.grant_achievement(user_id, "first_purchase"):
            await callback.message.answer("💰 ¡Logro desbloqueado: 'Primer Comprador'! ¡Felicidades por tu primera adquisición!")
    else:
        # If purchase failed, return to store menu or display details again
        reward = await reward_service.get_reward_by_id(reward_id)
        if reward:
            text = await get_reward_details_message(reward)
            await callback.message.edit_text(text, reply_markup=get_confirm_purchase_keyboard(reward_id), parse_mode="Markdown")
        else:
            await callback.message.edit_text("Algo salió mal. Vuelve a intentarlo.", reply_markup=get_main_menu_keyboard(), parse_mode="Markdown")

@router.message(F.text == "🏆 Ranking")
@router.message(Command("ranking"))
async def show_ranking(message: Message, session: AsyncSession):
    offset = 0
    stmt = select(User).order_by(User.points.desc()).offset(offset).limit(10)
    result = await session.execute(stmt)
    top_users = result.scalars().all()

    total_users_stmt = select(func.count(User.id))
    total_users_result = await session.execute(total_users_stmt)
    total_users = total_users_result.scalar_one()

    if not top_users:
        await message.answer("Aún no hay usuarios en el ranking. ¡Sé el primero en la cima! 🚀", reply_markup=get_ranking_keyboard())
        return

    ranking_text = "🏆 **Ranking de Usuarios (Top 10):**\n\n"
    for i, user in enumerate(top_users):
        ranking_text += f"`{offset + i + 1}.` {user.first_name or user.username} - `{user.points}` puntos (Nivel `{user.level}`)\n"

    await message.answer(ranking_text, reply_markup=get_ranking_keyboard(offset, total_users), parse_mode="Markdown")

@router.callback_query(F.data.startswith("ranking_nav_"))
async def navigate_ranking(callback: CallbackQuery, session: AsyncSession):
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
        ranking_text += f"`{offset + i + 1}.` {user.first_name or user.username} - `{user.points}` puntos (Nivel `{user.level}`)\n"

    await callback.message.edit_text(ranking_text, reply_markup=get_ranking_keyboard(offset, total_users), parse_mode="Markdown")
    await callback.answer()

