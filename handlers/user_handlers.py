# handlers/user_handlers.py - Bloque 1 de 2
import datetime
from aiogram import Router, F, Bot  # Asegúrate de importar Bot aquí
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton  # Import for external actions in channel
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
        for ach_id, ach_data in user_achievements.items():
            if ach_id in ACHIEVEMENTS:
                granted_achievements_list.append({
                    "id": ach_id,
                    "name": ach_data['name'],
                    "icon": ach_data['icon'],
                    "granted_at": ach_data['granted_at']
                })
        granted_achievements_list.sort(key=lambda x: x['granted_at'], reverse=True)
        achievements_formatted = [
            f"{ach['icon']} `{ach['name']}` (Desbloqueado el: `{datetime.datetime.fromisoformat(ach['granted_at']).strftime('%d/%m/%Y')}`)"
            for ach in granted_achievements_list
        ]
        achievements_text = "🏆 **Tus Logros Desbloqueados:**\n\n" + "\n".join(achievements_formatted)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Volver al Perfil", callback_data="show_profile_menu")]
    ])
    await callback.message.edit_text(achievements_text, parse_mode="Markdown", reply_markup=keyboard)
    await callback.answer()
    @router.callback_query(F.data == "show_profile_menu")
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
@router.callback_query(F.data == "profile_missions_active")
@router.callback_query(F.data.startswith("missions_nav_"))
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

# (... continúa con más funciones como show_mission_details, complete_mission, show_rewards, etc. ...)
