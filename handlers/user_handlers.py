# handlers/user_handlers.py - Bloque 1 de 2

import datetime
from aiogram import Router, F, Bot  # Asegúrate de importar Bot aquí
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton  # Import for external actions in channel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from database.models import User, Mission, Reward
from utils.keyboard_utils import (
    get_main_menu_keyboard,
    get_missions_keyboard,
    get_reward_keyboard,
    get_confirm_purchase_keyboard,
    get_ranking_keyboard
)
from services.point_service import (
    add_points,
    get_user_points,
    get_top_users,
    record_purchase
)
from services.level_service import (
    get_user_level,
    get_level_threshold
)
from services.mission_service import (
    get_available_missions,
    complete_mission
)
from services.reward_service import (
    get_available_rewards,
    redeem_reward
)

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession):
    """Maneja el comando /start y registra al usuario si no existe."""
    stmt = select(User).where(User.id == message.from_user.id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        user = User(
            id=message.from_user.id,
            username=message.from_user.username or "SinUsername",
            join_date=datetime.datetime.utcnow()
        )
        session.add(user)
        await session.commit()
    await message.answer(
        f"¡Hola {message.from_user.first_name}! Bienvenido al Canal VIP.",
        reply_markup=get_main_menu_keyboard()
    )

@router.message(Command("menu"))
async def cmd_menu(message: Message):
    """Muestra el menú principal."""
    await message.answer("Menú principal:", reply_markup=get_main_menu_keyboard())

@router.message(Command("misiones"))
async def cmd_missions(message: Message, session: AsyncSession):
    """Muestra las misiones disponibles."""
    missions = await get_available_missions(session, message.from_user.id)
    await message.answer(
        "Elige una misión:",
        reply_markup=get_missions_keyboard(missions)
    )

@router.callback_query(F.data.startswith("mission_"))
async def cq_select_mission(callback: CallbackQuery, session: AsyncSession):
    """Selecciona una misión y la marca como completada tras confirmar."""
    mission_id = int(callback.data.split("_")[1])
    points_awarded = await complete_mission(session, callback.from_user.id, mission_id)
    await callback.message.edit_text(
        f"Misión completada, ganaste {points_awarded} puntos.",
        reply_markup=get_main_menu_keyboard()
    )

@router.message(Command("tienda"))
async def cmd_store(message: Message, session: AsyncSession):
    """Muestra la tienda de recompensas."""
    rewards = await get_available_rewards(session)
    await message.answer(
        "Catálogo de recompensas:",
        reply_markup=get_reward_keyboard(rewards)
    )

@router.callback_query(F.data.startswith("reward_"))
async def cq_select_reward(callback: CallbackQuery, session: AsyncSession):
    """Muestra confirmación de compra para la recompensa seleccionada."""
    reward_id = int(callback.data.split("_")[1])
    await callback.message.edit_text(
        "¿Confirmas que deseas canjear esta recompensa?",
        reply_markup=get_confirm_purchase_keyboard(reward_id)
    )

@router.callback_query(F.data.startswith("confirm_purchase_"))
async def cq_confirm_purchase(callback: CallbackQuery, session: AsyncSession):
    """Procesa la compra de la recompensa si el usuario tiene puntos suficientes."""
    reward_id = int(callback.data.split("_")[1])
    user_points = await get_user_points(session, callback.from_user.id)
    reward = await session.get(Reward, reward_id)
    if user_points >= reward.cost:
        await record_purchase(session, callback.from_user.id, reward_id)
        await add_points(session, callback.from_user.id, -reward.cost)
        await callback.message.edit_text(
            f"Recompensa {reward.name} adquirida. Te quedan {user_points - reward.cost} puntos.",
            reply_markup=get_main_menu_keyboard()
        )
    else:
        await callback.message.edit_text(
            "No tienes suficientes puntos para esta recompensa.",
            reply_markup=get_main_menu_keyboard()
)# handlers/user_handlers.py - Bloque 2 de 2

@router.callback_query(F.data == "cancel_purchase")
async def cq_cancel_purchase(callback: CallbackQuery):
    """Cancela el proceso de compra y regresa al menú."""
    await callback.message.edit_text(
        "Compra cancelada.",
        reply_markup=get_main_menu_keyboard()
    )

@router.message(Command("ranking"))
async def cmd_ranking(message: Message):
    """Muestra el ranking de usuarios basado en puntos."""
    top_users = await get_top_users(10)
    text = "🏆 Top 10 Usuarios 🏆\n"
    for idx, user in enumerate(top_users, start=1):
        text += f"{idx}. {user.username}: {user.points} pts\n"
    await message.answer(text, reply_markup=get_ranking_keyboard())

@router.message(Command("perfil"))
async def cmd_profile(message: Message, session: AsyncSession):
    """Muestra perfil de usuario con puntos y nivel."""
    points = await get_user_points(session, message.from_user.id)
    level = await get_user_level(session, message.from_user.id)
    threshold = get_level_threshold(level + 1)
    await message.answer(
        f"Perfil de {message.from_user.first_name}:\n"
        f"Nivel: {level}\n"
        f"Puntos: {points}/{threshold}",
        reply_markup=get_main_menu_keyboard()
    )

@router.message(Command("misiones_activas"))
async def cmd_active_missions(message: Message, session: AsyncSession):
    """Muestra misiones ya iniciadas/completadas."""
    # Implementación pendiente o existente...
    pass

@router.message(Command("stats"))
async def cmd_stats(message: Message, session: AsyncSession):
    """Estadísticas avanzadas de usuario."""
    # Ejemplo: mostrar número de misiones completadas, compras, etc.
    pass

# Aquí podrías continuar con más handlers, por ejemplo noticias, ayuda, etc.
# handlers/user_handlers.py - Bloque 2 de 2

@router.callback_query(F.data == "cancel_purchase")
async def cq_cancel_purchase(callback: CallbackQuery):
    """Cancela el proceso de compra y regresa al menú."""
    await callback.message.edit_text(
        "Compra cancelada.",
        reply_markup=get_main_menu_keyboard()
    )

@router.message(Command("ranking"))
async def cmd_ranking(message: Message):
    """Muestra el ranking de usuarios basado en puntos."""
    top_users = await get_top_users(10)
    text = "🏆 Top 10 Usuarios 🏆\n"
    for idx, user in enumerate(top_users, start=1):
        text += f"{idx}. {user.username}: {user.points} pts\n"
    await message.answer(text, reply_markup=get_ranking_keyboard())

@router.message(Command("perfil"))
async def cmd_profile(message: Message, session: AsyncSession):
    """Muestra perfil de usuario con puntos y nivel."""
    points = await get_user_points(session, message.from_user.id)
    level = await get_user_level(session, message.from_user.id)
    threshold = get_level_threshold(level + 1)
    await message.answer(
        f"Perfil de {message.from_user.first_name}:\n"
        f"Nivel: {level}\n"
        f"Puntos: {points}/{threshold}",
        reply_markup=get_main_menu_keyboard()
    )

@router.message(Command("misiones_activas"))
async def cmd_active_missions(message: Message, session: AsyncSession):
    """Muestra misiones ya iniciadas/completadas."""
    # Implementación pendiente o existente...
    pass

@router.message(Command("stats"))
async def cmd_stats(message: Message, session: AsyncSession):
    """Estadísticas avanzadas de usuario."""
    # Ejemplo: mostrar número de misiones completadas, compras, etc.
    pass

# Aquí podrías continuar con más handlers, por ejemplo noticias, ayuda, etc.
