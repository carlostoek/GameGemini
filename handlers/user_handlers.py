# handlers/user_handlers.py
import datetime
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
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
# ¡Añade esta importación!
from utils.message_utils import get_profile_message, get_mission_details_message, get_reward_details_message
from utils.messages import BOT_MESSAGES # <--- NUEVA IMPORTACIÓN
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
        # Usa el mensaje personalizado para nuevos usuarios
        welcome_text = BOT_MESSAGES["start_welcome_new_user"]
    else:
        # Usa el mensaje personalizado para usuarios que regresan
        welcome_text = BOT_MESSAGES["start_welcome_returning_user"]

    if message.from_user.id == message.chat.id:
        await message.answer(welcome_text, reply_markup=get_main_menu_keyboard(), parse_mode="Markdown")
    else:
        await message.answer(welcome_text, parse_mode="Markdown")


@router.message(F.text == "👤 Mi Perfil")
@router.message(Command("mispuntos"))
async def show_profile(message: Message, session: AsyncSession):
    user = await session.get(User, message.from_user.id)
    if not user:
        # Usa el mensaje personalizado
        await message.answer(BOT_MESSAGES["profile_not_registered"])
        return

    mission_service = MissionService(session)
    active_missions = await mission_service.get_active_missions(user.id)

    profile_text = await get_profile_message(user, active_missions)
    await message.answer(profile_text, reply_markup=get_profile_keyboard(), parse_mode="Markdown")


@router.callback_query(F.data == "profile_achievements")
async def show_achievements(callback: CallbackQuery, session: AsyncSession):
    user = await session.get(User, callback.from_user.id)
    if not user:
        await callback.answer(BOT_MESSAGES["reward_not_registered"], show_alert=True) # Reutilizando mensaje similar, o crear uno específico
        return

    achievement_service = AchievementService(session)
    granted_achievements_data = await achievement_service.get_user_achievements(user.id)

    if not granted_achievements_data:
        # Usa el mensaje personalizado
        achievements_text = BOT_MESSAGES["profile_no_achievements"]
    else:
        sorted_achievements = sorted(
            granted_achievements_data.values(),
            key=lambda x: datetime.datetime.fromisoformat(x['granted_at']),
            reverse=True
        )
        # Mantén este formato de logro, pero usa el título personalizado
        achievements_formatted = [f"{ach['icon']} `{ach['name']}` - Desbloqueado el `{datetime.datetime.fromisoformat(ach['granted_at']).strftime('%d/%m/%Y')}`" for ach in sorted_achievements]
        achievements_text = BOT_MESSAGES["profile_achievements_title"] + "\n\n" + "\n".join(achievements_formatted)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=BOT_MESSAGES["back_to_profile_button_text"], callback_data="show_profile")] # Usa texto personalizado
    ])
    await callback.message.edit_text(achievements_text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data == "show_profile")
async def back_to_profile(callback: CallbackQuery, session: AsyncSession):
    user = await session.get(User, callback.from_user.id)
    if not user:
        await callback.answer(BOT_MESSAGES["reward_not_registered"], show_alert=True) # Reutilizando
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
        await callback.answer(BOT_MESSAGES["reward_not_registered"], show_alert=True) # Reutilizando
        return

    mission_service = MissionService(session)
    active_missions = await mission_service.get_active_missions(user.id)

    if not active_missions:
        # Usa el mensaje personalizado
        missions_text = BOT_MESSAGES["profile_no_active_missions"]
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=BOT_MESSAGES["back_to_profile_button_text"], callback_data="show_profile")] # Usa texto personalizado
        ])
    else:
        missions_list_text = []
        for mission in active_missions:
            missions_list_text.append(f"- **{mission.name}** (`{mission.points_reward}` Pts)")
        # Usa el título personalizado
        missions_text = BOT_MESSAGES["profile_active_missions_title"] + "\n\n" + "\n".join(missions_list_text)

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=BOT_MESSAGES["view_all_missions_button_text"], callback_data="show_missions")], # Usa texto personalizado
            [InlineKeyboardButton(text=BOT_MESSAGES["back_to_profile_button_text"], callback_data="show_profile")] # Usa texto personalizado
        ])

    await callback.message.edit_text(missions_text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

@router.message(F.text == "🎯 Misiones")
@router.message(Command("misiones"))
async def show_missions(message: Message, session: AsyncSession):
    user = await session.get(User, message.from_user.id)
    if not user:
        await message.answer(BOT_MESSAGES["profile_not_registered"])
        return

    mission_service = MissionService(session)
    missions = await mission_service.get_active_missions(user.id)

    if not missions:
        await message.answer(BOT_MESSAGES["missions_no_active"],
                             reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=BOT_MESSAGES["back_to_main_menu_button_text"], callback_data="main_menu")]]), parse_mode="Markdown")
        return

    await message.answer(BOT_MESSAGES["missions_title"], reply_markup=get_missions_keyboard(missions, 0), parse_mode="Markdown")


@router.callback_query(F.data.startswith("missions_nav_"))
async def navigate_missions(callback: CallbackQuery, session: AsyncSession):
    offset = int(callback.data.split("_")[2])
    user = await session.get(User, callback.from_user.id)
    if not user:
        await callback.answer(BOT_MESSAGES["reward_not_registered"], show_alert=True)
        return

    mission_service = MissionService(session)
    missions = await mission_service.get_active_missions(user.id)

    if not missions:
        await callback.message.edit_text(BOT_MESSAGES["missions_no_active"],
                                         reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=BOT_MESSAGES["back_to_main_menu_button_text"], callback_data="main_menu")]]), parse_mode="Markdown")
        await callback.answer()
        return

    await callback.message.edit_text(BOT_MESSAGES["missions_title"], reply_markup=get_missions_keyboard(missions, offset), parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data.startswith("mission_"))
async def show_mission_details(callback: CallbackQuery, session: AsyncSession):
    mission_id = callback.data.split("_")[1]
    mission_service = MissionService(session)
    mission = await mission_service.get_mission_by_id(mission_id)

    if not mission:
        await callback.answer(BOT_MESSAGES["mission_not_found"], show_alert=True)
        return

    user = await session.get(User, callback.from_user.id)
    if not user:
        await callback.answer(BOT_MESSAGES["reward_not_registered"], show_alert=True)
        return

    is_completed_for_period, _ = await mission_service.check_mission_completion_status(user, mission)
    if is_completed_for_period:
        await callback.answer(BOT_MESSAGES["mission_already_completed"], show_alert=True)
        return

    mission_text = await get_mission_details_message(mission)
    complete_button = []
    if not mission.requires_action:
        complete_button.append([InlineKeyboardButton(text=BOT_MESSAGES["complete_mission_button_text"], callback_data=f"complete_mission_{mission_id}")])

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        *complete_button,
        [InlineKeyboardButton(text=BOT_MESSAGES["back_to_missions_button_text"], callback_data=f"show_missions")]
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
        user = await session.get(User, user_id)
        await point_service.add_points(user_id, mission.points_reward)
        leveled_up = await level_service.check_for_level_up(user)

        response_text = BOT_MESSAGES["mission_completed_success"].format(mission_name=mission.name, points_reward=mission.points_reward)
        if leveled_up:
            response_text += BOT_MESSAGES["mission_level_up_bonus"].format(user_level=user.level)

        if mission_id == "first_mission_example_id": # Mantén esta lógica si es necesaria para el logro específico
            if await achievement_service.grant_achievement(user_id, "first_mission"):
                response_text += BOT_MESSAGES["mission_achievement_unlocked"].format(achievement_name=ACHIEVEMENTS["first_mission"]["name"]) # Usar el nombre del logro desde ACHIEVEMENTS

        await callback.message.edit_text(response_text, reply_markup=get_profile_keyboard(), parse_mode="Markdown")
    else:
        response_text = BOT_MESSAGES["mission_completion_failed"]
        await callback.answer(response_text, show_alert=True)

    await callback.answer()


@router.message(F.text == "🛍️ Tienda de Recompensas")
@router.message(Command("tienda"))
async def show_rewards(message: Message, session: AsyncSession):
    user = await session.get(User, message.from_user.id)
    if not user:
        await message.answer(BOT_MESSAGES["profile_not_registered"])
        return

    reward_service = RewardService(session)
    rewards = await reward_service.get_active_rewards()

    if not rewards:
        await message.answer(BOT_MESSAGES["reward_shop_empty"],
                             reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=BOT_MESSAGES["back_to_main_menu_button_text"], callback_data="main_menu")]]), parse_mode="Markdown")
        return

    await message.answer(BOT_MESSAGES["reward_shop_title"], reply_markup=get_reward_keyboard(rewards, 0), parse_mode="Markdown")


@router.callback_query(F.data.startswith("rewards_nav_"))
async def navigate_rewards(callback: CallbackQuery, session: AsyncSession):
    offset = int(callback.data.split("_")[2])
    reward_service = RewardService(session)
    rewards = await reward_service.get_active_rewards()

    if not rewards:
        await callback.message.edit_text(BOT_MESSAGES["reward_shop_empty"],
                                         reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=BOT_MESSAGES["back_to_main_menu_button_text"], callback_data="main_menu")]]), parse_mode="Markdown")
        await callback.answer()
        return

    await callback.message.edit_text(BOT_MESSAGES["reward_shop_title"], reply_markup=get_reward_keyboard(rewards, offset), parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data.startswith("reward_"))
async def show_reward_details(callback: CallbackQuery, session: AsyncSession):
    reward_id = int(callback.data.split("_")[1])
    reward_service = RewardService(session)
    reward = await reward_service.get_reward_by_id(reward_id)

    if not reward or not reward.is_active:
        await callback.answer(BOT_MESSAGES["reward_not_found"], show_alert=True)
        return

    user = await session.get(User, callback.from_user.id)
    if not user:
        await callback.answer(BOT_MESSAGES["reward_not_registered"], show_alert=True)
        return

    reward_text = await get_reward_details_message(reward, user.points)
    await callback.message.edit_text(reward_text, reply_markup=get_confirm_purchase_keyboard(reward_id, reward.cost), parse_mode="Markdown") # Pasamos reward.cost aquí
    await callback.answer()


@router.callback_query(F.data.startswith("purchase_"))
async def confirm_purchase(callback: CallbackQuery, session: AsyncSession):
    reward_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id

    reward_service = RewardService(session)
    success, message_key = await reward_service.purchase_reward(user_id, reward_id) # message_key ahora es una clave del diccionario

    user = await session.get(User, user_id) # Para obtener puntos actualizados si es necesario
    reward = await reward_service.get_reward_by_id(reward_id) # Para obtener el costo si el mensaje lo necesita

    if success:
        message_to_send = BOT_MESSAGES[message_key] # Obtener el mensaje real
        await callback.message.delete()
        await callback.message.answer(message_to_send, reply_markup=get_main_menu_keyboard(), parse_mode="Markdown")
    else:
        # Aquí, message_key podría ser directamente el texto si el error es genérico o la clave del mensaje
        message_to_send = BOT_MESSAGES[message_key]
        if message_key == "reward_not_enough_points":
            message_to_send = message_to_send.format(required_points=reward.cost, user_points=user.points)
        await callback.message.edit_text(message_to_send, reply_markup=get_confirm_purchase_keyboard(reward_id, reward.cost), parse_mode="Markdown")
    await callback.answer()


@router.message(F.text == "🏆 Ranking")
@router.message(Command("ranking"))
async def show_ranking(message: Message, session: AsyncSession):
    user_id = message.from_user.id
    offset = 0

    total_users_stmt = select(func.count(User.id))
    total_users_result = await session.execute(total_users_stmt)
    total_users = total_users_result.scalar_one()

    stmt = select(User).order_by(User.points.desc(), User.id.asc()).offset(offset).limit(10)
    result = await session.execute(stmt)
    top_users = result.scalars().all()

    if not top_users:
        await message.answer(BOT_MESSAGES["ranking_no_users"], reply_markup=get_ranking_keyboard(), parse_mode="Markdown")
        return

    ranking_text = BOT_MESSAGES["ranking_title"] + "\n\n"

    ranking_entries = []
    for i, user in enumerate(top_users):
        display_name = ""
        if user.id == user_id:
            display_name = user.first_name or user.username or "Tú"
            display_name = display_name.replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace('`', '\\`')
        else:
            if user.username:
                display_name = f"@{user.username[0]}\\*****"
            elif user.first_name:
                display_name = f"{user.first_name[0]}\\*****"
            else:
                display_name = "Usuario Anónimo"

        ranking_entries.append(
            f"`#{offset + i + 1}.` {display_name} (`{user.points}` Pts, Nv. `{user.level}`)"
        )

    ranking_text += "\n".join(ranking_entries)

    await message.answer(ranking_text, reply_markup=get_ranking_keyboard(offset, total_users), parse_mode="Markdown")


@router.callback_query(F.data.startswith("ranking_nav_"))
async def navigate_ranking(callback: CallbackQuery, session: AsyncSession):
    user_id = callback.from_user.id
    offset = int(callback.data.split("_")[2])

    total_users_stmt = select(func.count(User.id))
    total_users_result = await session.execute(total_users_stmt)
    total_users = total_users_result.scalar_one()

    stmt = select(User).order_by(User.points.desc(), User.id.asc()).offset(offset).limit(10)
    result = await session.execute(stmt)
    top_users = result.scalars().all()

    if not top_users:
        await callback.message.edit_text(BOT_MESSAGES["ranking_no_users"], reply_markup=get_ranking_keyboard(), parse_mode="Markdown")
        await callback.answer()
        return

    ranking_text = BOT_MESSAGES["ranking_title"] + "\n\n"

    ranking_entries = []
    for i, user in enumerate(top_users):
        display_name = ""
        if user.id == user_id:
            display_name = user.first_name or user.username or "Tú"
            display_name = display_name.replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace('`', '\\`')
        else:
            if user.username:
                display_name = f"@{user.username[0]}\\*****"
            elif user.first_name:
                display_name = f"{user.first_name[0]}\\*****"
            else:
                display_name = "Usuario Anónimo"

        ranking_entries.append(
            f"`#{offset + i + 1}.` {display_name} (`{user.points}` Pts, Nv. `{user.level}`)"
        )

    ranking_text += "\n".join(ranking_entries)

    await callback.message.edit_text(ranking_text, reply_markup=get_ranking_keyboard(offset, total_users), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "main_menu")
async def back_to_main_menu(callback: CallbackQuery, session: AsyncSession):
    user_id = callback.from_user.id
    user = await session.get(User, user_id)
    if not user:
        await callback.answer(BOT_MESSAGES["reward_not_registered"], show_alert=True)
        return

    try:
        await callback.message.delete()
    except Exception as e:
        print(f"Error deleting message in back_to_main_menu: {e}")
        pass

    menu_message = BOT_MESSAGES["back_to_main_menu"]
    await callback.message.answer(menu_message, reply_markup=get_main_menu_keyboard(), parse_mode="Markdown")
    await callback.answer()
                       
