# handlers/user_handlers.py — Bloque 1 de 2

import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models import User, Mission, Reward
from utils.keyboard_utils import (
    get_main_menu_keyboard,
    get_profile_keyboard,
    get_missions_keyboard,
    get_reward_keyboard,
    get_confirm_purchase_keyboard,
    get_ranking_keyboard,
    get_reaction_keyboard
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
    """Maneja /start y registra al usuario."""
    stmt = select(User).where(User.id == message.from_user.id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        user = User(
            id=message.from_user.id,
            username=message.from_user.username or "SinUsername",
            join_date=datetime.datetime.utcnow(),
            points=0
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
    """Marca misión como completada y otorga puntos."""
    mission_id = int(callback.data.split("_")[1])
    points = await complete_mission(session, callback.from_user.id, mission_id)
    await callback.message.edit_text(
        f"Misión completada, ganaste {points} puntos.",
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
    # handlers/user_handlers.py — Bloque 2 de 2

@router.callback_query(F.data.startswith("reward_"))
async def cq_select_reward(callback: CallbackQuery, session: AsyncSession):
    """Pregunta al usuario si confirma la compra."""
    reward_id = int(callback.data.split("_")[1])
    await callback.message.edit_text(
        "¿Confirmas que deseas canjear esta recompensa?",
        reply_markup=get_confirm_purchase_keyboard(reward_id)
    )

@router.callback_query(F.data.startswith("confirm_purchase_"))
async def cq_confirm_purchase(callback: CallbackQuery, session: AsyncSession):
    """Procesa el canje de la recompensa."""
    reward_id = int(callback.data.split("_")[2])
    success = await redeem_reward(session, callback.from_user.id, reward_id)
    if success:
        points = await get_user_points(session, callback.from_user.id)
        await callback.message.edit_text(
            f"Recompensa adquirida. Te quedan {points} puntos.",
            reply_markup=get_main_menu_keyboard()
        )
    else:
        await callback.message.edit_text(
            "No tienes suficientes puntos o recompensa inactiva.",
            reply_markup=get_main_menu_keyboard()
        )

@router.callback_query(F.data == "cancel_purchase")
async def cq_cancel_purchase(callback: CallbackQuery):
    """Cancela el proceso de compra."""
    await callback.message.edit_text(
        "Compra cancelada.",
        reply_markup=get_main_menu_keyboard()
    )

@router.message(Command("ranking"))
async def cmd_ranking(message: Message, session: AsyncSession):
    """Muestra ranking de los top usuarios."""
    top_users = await get_top_users(session, 10)
    text = "🏆 Top 10 Usuarios 🏆\n"
    for i, u in enumerate(top_users, start=1):
        text += f"{i}. {u.username}: {u.points} pts\n"
    await message.answer(text, reply_markup=get_ranking_keyboard())

@router.message(Command("perfil"))
async def cmd_profile(message: Message, session: AsyncSession):
    """Muestra perfil con nivel y puntos."""
    points = await get_user_points(session, message.from_user.id)
    level = await get_user_level(session, message.from_user.id)
    next_thr = get_level_threshold(level + 1)
    await message.answer(
        f"Perfil de {message.from_user.first_name}:\n"
        f"Nivel: {level}\n"
        f"Puntos: {points}/{next_thr}",
        reply_markup=get_main_menu_keyboard()
    )

@router.message(Command("misiones_activas"))
async def cmd_active_missions(message: Message, session: AsyncSession):
    """Muestra misiones activas o completadas."""
    # Implementación existente o pendiente
    pass

@router.message(Command("stats"))
async def cmd_stats(message: Message, session: AsyncSession):
    """Estadísticas avanzadas del usuario."""
    # Ejemplo: número de misiones completadas, compras realizadas, etc.
    pass

# Puedes añadir aquí más handlers específicos según necesites.
