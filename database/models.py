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

# ... (el resto del archivo continúa sin alteraciones)
