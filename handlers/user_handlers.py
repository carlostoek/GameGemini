import logging
from aiogram import Router, types, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.enums import ParseMode

from database.models import User, Mission, Reward  # Mission y Reward ya incluidos en models
from services.point_service import add_points, deduct_points, get_points, get_point_logs
from services.level_service import get_level_by_points, get_progress_to_next_level
from services.achievement_service import check_and_award_achievements

from utils.keyboard_utils import get_main_menu_keyboard, get_missions_keyboard, get_reward_keyboard
from utils.message_utils import send_progress_bar, send_achievements_gallery
from utils.messages import WELCOME_MESSAGE, MISSION_COMPLETE_MESSAGE, POINTS_LIMIT_MESSAGE

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import datetime

router = Router()

logger = logging.getLogger(__name__)

# --- FUNCIONES AUXILIARES ---
async def get_or_create_user(session: AsyncSession, telegram_id, username=None):
    result = await session.execute(
        select(User).where(User.id == int(telegram_id))
    )
    user = result.scalar()
    if not user:
        user = User(
            id=int(telegram_id),
            username=username,
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
            points=0,
            level=1
        )
        session.add(user)
        await session.commit()
    return user

# --- HANDLERS ---

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, session: AsyncSession):
    user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
    await message.answer(
        WELCOME_MESSAGE,
        reply_markup=get_main_menu_keyboard()
    )

@router.message(Command("mispuntos"))
async def cmd_mispuntos(message: Message, session: AsyncSession):
    user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
    progress = get_progress_to_next_level(user.points)
    await message.answer(
        f"👑 *Nivel:* {progress['current_level']}\n"
        f"⭐️ *Puntos:* {progress['current_points']}\n"
        f"📈 *Siguiente nivel:* {progress['next_level']} ({progress['points_to_next']} puntos restantes)\n"
        f"Progreso: {progress['percent']}%",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_main_menu_keyboard()
    )
    await send_progress_bar(message, progress['percent'])
    await send_achievements_gallery(message, session, user)

@router.message(Command("ranking"))
async def cmd_ranking(message: Message, session: AsyncSession):
    # Top 10 ranking
    result = await session.execute(
        select(User).order_by(User.points.desc()).limit(10)
    )
    top_users = result.scalars().all()
    rank_lines = []
    for idx, u in enumerate(top_users, start=1):
        uname = u.username or u.id
        rank_lines.append(f"{idx}. {uname} - {u.points} puntos")
    await message.answer(
        "*🏆 Ranking TOP 10:*\n" + "\n".join(rank_lines),
        parse_mode=ParseMode.MARKDOWN
    )

@router.message(Command("canjear"))
async def cmd_canjear(message: Message, session: AsyncSession):
    result = await session.execute(
        select(Reward).where(Reward.is_active == True)
    )
    rewards = result.scalars().all()
    if not rewards:
        await message.answer("No hay recompensas activas por ahora.")
        return
    await message.answer(
        "🎁 *Catálogo de Recompensas VIP:*",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_reward_keyboard(rewards)
    )

@router.callback_query(F.data.startswith("canjear_"))
async def callback_canjear_reward(callback: CallbackQuery, session: AsyncSession):
    reward_id = int(callback.data.split("_")[1])
    result = await session.execute(
        select(Reward).where(Reward.id == reward_id)
    )
    reward = result.scalar()
    user = await get_or_create_user(session, callback.from_user.id, callback.from_user.username)
    if user.points < reward.cost_in_points:
        await callback.answer("No tienes suficientes puntos para este canje.", show_alert=True)
        return
    await deduct_points(session, user.id, reward.cost_in_points, action_type="canje", description=f"Canjeó {reward.name}")
    await callback.answer(f"¡Canje realizado! {reward.name} - Pronto recibirás tu recompensa.")

@router.message(Command("misiones"))
async def cmd_misiones(message: Message, session: AsyncSession):
    result = await session.execute(
        select(Mission).where(Mission.is_active == True)
    )
    missions = result.scalars().all()
    if not missions:
        await message.answer("No hay misiones activas por ahora.")
        return
    await message.answer(
        "🔥 *Misiones activas:*",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_missions_keyboard(missions)
    )

@router.callback_query(F.data.startswith("mision_"))
async def callback_completar_mision(callback: CallbackQuery, session: AsyncSession):
    mission_id = int(callback.data.split("_")[1])
    result = await session.execute(
        select(Mission).where(Mission.id == mission_id)
    )
    mission = result.scalar()
    user = await get_or_create_user(session, callback.from_user.id, callback.from_user.username)
    puntos = 5  # o según config/misión
    await add_points(session, user.id, puntos, action_type="mission", description=f"Completó misión {mission.name}")
    await check_and_award_achievements(session, user)
    await callback.answer(MISSION_COMPLETE_MESSAGE)

# Continúa en el siguiente bloque...

# --- Ejemplo de interacción con reacciones ---
@router.callback_query(F.data.startswith("react_"))
async def callback_reaccionar(callback: CallbackQuery, session: AsyncSession):
    reaction_type = callback.data.split("_", 1)[1]
    user = await get_or_create_user(session, callback.from_user.id, callback.from_user.username)
    puntos = 5
    await add_points(session, user.id, puntos, action_type="reaction", description=f"Reacción: {reaction_type}")
    await check_and_award_achievements(session, user)
    await callback.answer("¡Puntos ganados por interactuar!")

# --- Handler para participación en encuestas ---
@router.callback_query(F.data.startswith("encuesta_"))
async def callback_participar_encuesta(callback: CallbackQuery, session: AsyncSession):
    encuesta_id = callback.data.split("_")[1]
    user = await get_or_create_user(session, callback.from_user.id, callback.from_user.username)
    puntos = 5
    await add_points(session, user.id, puntos, action_type="encuesta", description=f"Participó en encuesta {encuesta_id}")
    await check_and_award_achievements(session, user)
    await callback.answer("¡Gracias por participar en la encuesta! Has ganado puntos.")

# --- Handler para referidos (esqueleto, puedes expandir lógica) ---
@router.message(Command("referido"))
async def cmd_referido(message: Message, session: AsyncSession):
    user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
    await message.answer("Funcionalidad de referidos en desarrollo.")

# --- Handler para admin sumar puntos manualmente ---
@router.message(Command("sumarpuntos"))
async def cmd_sumarpuntos(message: Message, session: AsyncSession):
    user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
    if not getattr(user, "is_admin", False):
        await message.answer("No tienes permisos para este comando.")
        return
    try:
        # /sumarpuntos <telegram_id> <puntos>
        _, target_id, puntos = message.text.split()
        target_user = await get_or_create_user(session, target_id)
        puntos = int(puntos)
    except Exception:
        await message.answer("Uso: /sumarpuntos <telegram_id> <puntos>")
        return

    await add_points(session, target_user.id, puntos, action_type="admin", description="Admin manual")
    await message.answer(f"Se sumaron {puntos} puntos a {target_user.username or target_user.id}.")

# --- Handler para admin restar puntos manualmente ---
@router.message(Command("restapuntos"))
async def cmd_restapuntos(message: Message, session: AsyncSession):
    user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
    if not getattr(user, "is_admin", False):
        await message.answer("No tienes permisos para este comando.")
        return
    try:
        # /restapuntos <telegram_id> <puntos>
        _, target_id, puntos = message.text.split()
        target_user = await get_or_create_user(session, target_id)
        puntos = int(puntos)
    except Exception:
        await message.answer("Uso: /restapuntos <telegram_id> <puntos>")
        return

    await deduct_points(session, target_user.id, puntos, action_type="admin_deduct", description="Admin manual")
    await message.answer(f"Se restaron {puntos} puntos a {target_user.username or target_user.id}.")

# --- Cualquier otro handler personalizado tuyo aquí abajo con la nueva lógica ---

# --- Fin del archivo ---
