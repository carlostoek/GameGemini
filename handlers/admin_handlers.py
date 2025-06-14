# handlers/admin_handlers.py - Bloque 1 de 2
import json
import csv
import io
import datetime

from aiogram import Router, F, Bot # Asegúrate de que Bot esté importado
from aiogram.types import Message, CallbackQuery, InputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from database.models import User, Reward, Mission, Event
from services.point_service import PointService
from services.reward_service import RewardService
from services.mission_service import MissionService
from services.level_service import LevelService # Not directly used here, but good to have
from utils.keyboard_utils import (
    get_admin_main_keyboard,
    get_main_menu_keyboard,
    get_reaction_keyboard,
    get_admin_manage_content_keyboard,
    get_admin_content_missions_keyboard,
    get_admin_content_badges_keyboard,
    get_admin_content_levels_keyboard,
    get_admin_content_rewards_keyboard,
    get_admin_content_auctions_keyboard,
    get_admin_content_daily_gifts_keyboard,
    get_back_keyboard,
    get_admin_users_list_keyboard,
)
from utils.message_utils import get_profile_message
from config import Config
import logging # <--- NUEVA IMPORTACIÓN

logger = logging.getLogger(__name__) # <--- NUEVA LÍNEA

router = Router()

# FSM States for Admin actions
class AdminStates(StatesGroup):
    creating_reward_name = State()
    creating_reward_description = State()
    creating_reward_cost = State()
    creating_reward_stock = State()

    creating_mission_name = State()
    creating_mission_description = State()
    creating_mission_points = State()
    creating_mission_type = State()
    creating_mission_requires_action = State()
    creating_mission_action_data = State()

    activating_event_name = State()
    activating_event_description = State()
    activating_event_multiplier = State()
    activating_event_duration = State() # In hours

    assigning_points_target = State()
    assigning_points_amount = State()

    # ¡NUEVO ESTADO FSM para enviar mensajes al canal con reacciones!
    waiting_for_channel_post_text = State()

    # States for user management actions
    view_user_identifier = State()
    search_user_query = State()
    notify_users_text = State()


async def show_users_page(message: Message, session: AsyncSession, offset: int) -> None:
    """Display a paginated list of users with action buttons."""
    limit = 5
    if offset < 0:
        offset = 0

    total_stmt = select(func.count()).select_from(User)
    total_result = await session.execute(total_stmt)
    total_users = total_result.scalar_one()

    stmt = (
        select(User)
        .order_by(User.id)
        .offset(offset)
        .limit(limit)
    )
    result = await session.execute(stmt)
    users = result.scalars().all()

    text_lines = [
        "👥 *Gestionar Usuarios*",
        f"Mostrando {offset + 1}-{min(offset + limit, total_users)} de {total_users}",
        "",
    ]

    for user in users:
        display = user.username or (user.first_name or "Sin nombre")
        text_lines.append(f"- {display} (ID: {user.id}) - {user.points} pts")

    keyboard = get_admin_users_list_keyboard(users, offset, total_users, limit)

    await message.edit_text(
        "\n".join(text_lines), reply_markup=keyboard, parse_mode="Markdown"
    )


@router.message(Command("admin"))
async def admin_panel(message: Message):
    if message.from_user.id != Config.ADMIN_ID:
        await message.answer("Acceso denegado. No eres administrador.")
        return
    await message.answer(
        "Bienvenido al panel de administración, Diana.",
        reply_markup=get_admin_main_keyboard(),
    )


@router.callback_query(F.data == "admin_manage_users")
async def admin_manage_users(callback: CallbackQuery, session: AsyncSession):
    if callback.from_user.id != Config.ADMIN_ID:
        await callback.answer("Acceso denegado", show_alert=True)
        return

    await show_users_page(callback.message, session, 0)
    await callback.answer()


@router.callback_query(F.data.startswith("admin_users_page_"))
async def admin_users_page(callback: CallbackQuery, session: AsyncSession):
    if callback.from_user.id != Config.ADMIN_ID:
        await callback.answer("Acceso denegado", show_alert=True)
        return

    try:
        offset = int(callback.data.split("_")[-1])
    except ValueError:
        offset = 0

    await show_users_page(callback.message, session, offset)
    await callback.answer()

@router.callback_query(F.data == "admin_main_menu")
async def admin_back_to_main_menu(callback: CallbackQuery):
    if callback.from_user.id != Config.ADMIN_ID:
        await callback.answer("Acceso denegado", show_alert=True)
        return
    await callback.message.edit_text(
        "Bienvenido al panel de administración, Diana.",
        reply_markup=get_admin_main_keyboard(),
    )
    await callback.answer()

@router.callback_query(F.data == "admin_add_points")
async def admin_add_points(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != Config.ADMIN_ID:
        await callback.answer("Acceso denegado", show_alert=True)
        return
    await callback.message.edit_text(
        "Ingresa el ID de usuario o el username (con @) al que deseas **sumar** puntos:",
        parse_mode="Markdown",
        reply_markup=get_back_keyboard("admin_manage_users"),
    )
    await state.update_data(points_operation="add")
    await state.set_state(AdminStates.assigning_points_target)
    await callback.answer()

@router.callback_query(F.data == "admin_deduct_points")
async def admin_deduct_points(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != Config.ADMIN_ID:
        await callback.answer("Acceso denegado", show_alert=True)
        return
    await callback.message.edit_text(
        "Ingresa el ID de usuario o el username (con @) al que deseas **restar** puntos:",
        parse_mode="Markdown",
        reply_markup=get_back_keyboard("admin_manage_users"),
    )
    await state.update_data(points_operation="deduct")
    await state.set_state(AdminStates.assigning_points_target)
    await callback.answer()

@router.callback_query(F.data == "admin_view_user")
async def admin_view_user(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != Config.ADMIN_ID:
        await callback.answer("Acceso denegado", show_alert=True)
        return
    await callback.message.edit_text(
        "Envía el ID de usuario o username (@) para ver su perfil:",
        parse_mode="Markdown",
        reply_markup=get_back_keyboard("admin_manage_users"),
    )
    await state.set_state(AdminStates.view_user_identifier)
    await callback.answer()

@router.message(AdminStates.view_user_identifier)
async def admin_process_view_user(message: Message, state: FSMContext, session: AsyncSession):
    if message.from_user.id != Config.ADMIN_ID:
        return
    identifier = message.text.strip()
    user = None
    if identifier.isdigit():
        user = await session.get(User, int(identifier))
    elif identifier.startswith('@'):
        stmt = select(User).where(User.username == identifier[1:])
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

    if not user:
        await message.answer("Usuario no encontrado.")
    else:
        mission_service = MissionService(session)
        active_missions = await mission_service.get_active_missions(user_id=user.id)
        profile_text = await get_profile_message(user, active_missions)
        await message.answer(profile_text, parse_mode="Markdown")
    await state.clear()


@router.callback_query(F.data.startswith("admin_user_add_"))
async def admin_quick_add_points(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != Config.ADMIN_ID:
        await callback.answer("Acceso denegado", show_alert=True)
        return

    user_id = int(callback.data.split("_")[-1])
    await state.update_data(points_operation="add", target_user_identifier=str(user_id))
    await callback.message.answer(
        f"Ingresa la cantidad de puntos a **sumar** a `{user_id}`:",
        parse_mode="Markdown",
        reply_markup=get_back_keyboard("admin_manage_users"),
    )
    await state.set_state(AdminStates.assigning_points_amount)
    await callback.answer()


@router.callback_query(F.data.startswith("admin_user_deduct_"))
async def admin_quick_deduct_points(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != Config.ADMIN_ID:
        await callback.answer("Acceso denegado", show_alert=True)
        return

    user_id = int(callback.data.split("_")[-1])
    await state.update_data(points_operation="deduct", target_user_identifier=str(user_id))
    await callback.message.answer(
        f"Ingresa la cantidad de puntos a **restar** a `{user_id}`:",
        parse_mode="Markdown",
        reply_markup=get_back_keyboard("admin_manage_users"),
    )
    await state.set_state(AdminStates.assigning_points_amount)
    await callback.answer()


@router.callback_query(F.data.startswith("admin_user_view_"))
async def admin_quick_view_profile(callback: CallbackQuery, session: AsyncSession):
    if callback.from_user.id != Config.ADMIN_ID:
        await callback.answer("Acceso denegado", show_alert=True)
        return

    user_id = int(callback.data.split("_")[-1])
    user = await session.get(User, user_id)
    if not user:
        await callback.answer("Usuario no encontrado", show_alert=True)
        return
    mission_service = MissionService(session)
    active_missions = await mission_service.get_active_missions(user_id=user.id)
    profile_text = await get_profile_message(user, active_missions)
    await callback.message.answer(profile_text, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "admin_search_user")
async def admin_search_user(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != Config.ADMIN_ID:
        await callback.answer("Acceso denegado", show_alert=True)
        return
    await callback.message.edit_text(
        "Ingresa un término de búsqueda (ID o nombre de usuario):",
        reply_markup=get_back_keyboard("admin_manage_users"),
    )
    await state.set_state(AdminStates.search_user_query)
    await callback.answer()

@router.message(AdminStates.search_user_query)
async def admin_process_search_user(message: Message, state: FSMContext, session: AsyncSession):
    if message.from_user.id != Config.ADMIN_ID:
        return
    query = message.text.strip()
    users = []
    if query.isdigit():
        user = await session.get(User, int(query))
        if user:
            users = [user]
    else:
        stmt = select(User).where(
            (User.username.ilike(f"%{query}%")) |
            (User.first_name.ilike(f"%{query}%")) |
            (User.last_name.ilike(f"%{query}%"))
        ).limit(10)
        result = await session.execute(stmt)
        users = result.scalars().all()

    if not users:
        await message.answer("No se encontraron usuarios.")
    else:
        response = "Resultados de búsqueda:\n\n"
        for u in users:
            display = u.username if u.username else (u.first_name or "")
            response += f"- {display} (ID: {u.id}) - {u.points} puntos\n"
        await message.answer(response)
    await state.clear()

@router.callback_query(F.data == "admin_notify_users")
async def admin_notify_users(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != Config.ADMIN_ID:
        await callback.answer("Acceso denegado", show_alert=True)
        return
    await callback.message.edit_text(
        "Escribe el mensaje que deseas enviar a todos los usuarios:",
        reply_markup=get_back_keyboard("admin_manage_users"),
    )
    await state.set_state(AdminStates.notify_users_text)
    await callback.answer()

@router.message(AdminStates.notify_users_text)
async def admin_process_notify_users(message: Message, state: FSMContext, session: AsyncSession, bot: Bot):
    if message.from_user.id != Config.ADMIN_ID:
        return
    text = message.text
    stmt = select(User.id)
    result = await session.execute(stmt)
    user_ids = [row[0] for row in result.all()]
    sent = 0
    for uid in user_ids:
        try:
            await bot.send_message(uid, text)
            sent += 1
        except Exception as e:
            logger.warning(f"No se pudo enviar notificación a {uid}: {e}")
    await message.answer(f"Notificación enviada a {sent} usuarios.", reply_markup=get_admin_main_keyboard())
    await state.clear()


@router.callback_query(F.data == "admin_manage_content")
async def admin_manage_content(callback: CallbackQuery):
    if callback.from_user.id != Config.ADMIN_ID:
        await callback.answer("Acceso denegado", show_alert=True)
        return
    await callback.message.edit_text(
        "🎮 *Gestionar Contenido / Juego* - Selecciona una categoría:",
        reply_markup=get_admin_manage_content_keyboard(),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data == "admin_content_missions")
async def admin_content_missions(callback: CallbackQuery):
    if callback.from_user.id != Config.ADMIN_ID:
        await callback.answer("Acceso denegado", show_alert=True)
        return
    await callback.message.edit_text(
        "📌 *Misiones* - Selecciona una opción:",
        reply_markup=get_admin_content_missions_keyboard(),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data == "admin_content_badges")
async def admin_content_badges(callback: CallbackQuery):
    if callback.from_user.id != Config.ADMIN_ID:
        await callback.answer("Acceso denegado", show_alert=True)
        return
    await callback.message.edit_text(
        "🏅 *Insignias* - Selecciona una opción:",
        reply_markup=get_admin_content_badges_keyboard(),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data == "admin_content_levels")
async def admin_content_levels(callback: CallbackQuery):
    if callback.from_user.id != Config.ADMIN_ID:
        await callback.answer("Acceso denegado", show_alert=True)
        return
    await callback.message.edit_text(
        "📈 *Niveles* - Selecciona una opción:",
        reply_markup=get_admin_content_levels_keyboard(),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data == "admin_content_rewards")
async def admin_content_rewards(callback: CallbackQuery):
    if callback.from_user.id != Config.ADMIN_ID:
        await callback.answer("Acceso denegado", show_alert=True)
        return
    await callback.message.edit_text(
        "🎁 *Recompensas (Catálogo VIP)* - Selecciona una opción:",
        reply_markup=get_admin_content_rewards_keyboard(),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data == "admin_content_auctions")
async def admin_content_auctions(callback: CallbackQuery):
    if callback.from_user.id != Config.ADMIN_ID:
        await callback.answer("Acceso denegado", show_alert=True)
        return
    await callback.message.edit_text(
        "📦 *Subastas* - Selecciona una opción:",
        reply_markup=get_admin_content_auctions_keyboard(),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data == "admin_content_daily_gifts")
async def admin_content_daily_gifts(callback: CallbackQuery):
    if callback.from_user.id != Config.ADMIN_ID:
        await callback.answer("Acceso denegado", show_alert=True)
        return
    await callback.message.edit_text(
        "🎁 *Regalos Diarios* - Selecciona una opción:",
        reply_markup=get_admin_content_daily_gifts_keyboard(),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data == "admin_toggle_mission")
async def admin_toggle_mission(callback: CallbackQuery):
    if callback.from_user.id != Config.ADMIN_ID:
        await callback.answer("Acceso denegado", show_alert=True)
        return
    await callback.message.edit_text(
        "Funcionalidad en desarrollo.",
        reply_markup=get_admin_content_missions_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "admin_view_active_missions")
async def admin_view_active_missions(callback: CallbackQuery):
    if callback.from_user.id != Config.ADMIN_ID:
        await callback.answer("Acceso denegado", show_alert=True)
        return
    await callback.message.edit_text(
        "Funcionalidad en desarrollo.",
        reply_markup=get_admin_content_missions_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "admin_give_badge_manual")
async def admin_give_badge_manual(callback: CallbackQuery):
    if callback.from_user.id != Config.ADMIN_ID:
        await callback.answer("Acceso denegado", show_alert=True)
        return
    await callback.message.edit_text(
        "Funcionalidad en desarrollo.",
        reply_markup=get_admin_content_badges_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "admin_manage_badges")
async def admin_manage_badges(callback: CallbackQuery):
    if callback.from_user.id != Config.ADMIN_ID:
        await callback.answer("Acceso denegado", show_alert=True)
        return
    await callback.message.edit_text(
        "Funcionalidad en desarrollo.",
        reply_markup=get_admin_content_badges_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "admin_adjust_levels")
async def admin_adjust_levels(callback: CallbackQuery):
    if callback.from_user.id != Config.ADMIN_ID:
        await callback.answer("Acceso denegado", show_alert=True)
        return
    await callback.message.edit_text(
        "Funcionalidad en desarrollo.",
        reply_markup=get_admin_content_levels_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "admin_edit_reward")
async def admin_edit_reward(callback: CallbackQuery):
    if callback.from_user.id != Config.ADMIN_ID:
        await callback.answer("Acceso denegado", show_alert=True)
        return
    await callback.message.edit_text(
        "Funcionalidad en desarrollo.",
        reply_markup=get_admin_content_rewards_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "admin_view_claimed_rewards")
async def admin_view_claimed_rewards(callback: CallbackQuery):
    if callback.from_user.id != Config.ADMIN_ID:
        await callback.answer("Acceso denegado", show_alert=True)
        return
    await callback.message.edit_text(
        "Funcionalidad en desarrollo.",
        reply_markup=get_admin_content_rewards_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "admin_create_auction")
async def admin_create_auction(callback: CallbackQuery):
    if callback.from_user.id != Config.ADMIN_ID:
        await callback.answer("Acceso denegado", show_alert=True)
        return
    await callback.message.edit_text(
        "Funcionalidad en desarrollo.",
        reply_markup=get_admin_content_auctions_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "admin_view_auctions")
async def admin_view_auctions(callback: CallbackQuery):
    if callback.from_user.id != Config.ADMIN_ID:
        await callback.answer("Acceso denegado", show_alert=True)
        return
    await callback.message.edit_text(
        "Funcionalidad en desarrollo.",
        reply_markup=get_admin_content_auctions_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "admin_finish_auction")
async def admin_finish_auction(callback: CallbackQuery):
    if callback.from_user.id != Config.ADMIN_ID:
        await callback.answer("Acceso denegado", show_alert=True)
        return
    await callback.message.edit_text(
        "Funcionalidad en desarrollo.",
        reply_markup=get_admin_content_auctions_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "admin_configure_daily_gift")
async def admin_configure_daily_gift(callback: CallbackQuery):
    if callback.from_user.id != Config.ADMIN_ID:
        await callback.answer("Acceso denegado", show_alert=True)
        return
    await callback.message.edit_text(
        "Funcionalidad en desarrollo.",
        reply_markup=get_admin_content_daily_gifts_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "admin_manage_events_sorteos")
async def admin_manage_events_sorteos(callback: CallbackQuery):
    if callback.from_user.id != Config.ADMIN_ID:
        await callback.answer("Acceso denegado", show_alert=True)
        return
    await callback.message.edit_text(
        "Gestión de eventos y sorteos en desarrollo.",
        reply_markup=get_admin_main_keyboard(),
    )
    await callback.answer()



@router.callback_query(F.data == "admin_bot_config")
async def admin_bot_config(callback: CallbackQuery):
    if callback.from_user.id != Config.ADMIN_ID:
        await callback.answer("Acceso denegado", show_alert=True)
        return
    await callback.message.edit_text(
        "Configuración del bot en desarrollo.", reply_markup=get_admin_main_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "admin_create_reward")
async def admin_start_create_reward(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != Config.ADMIN_ID: return
    await callback.message.edit_text(
        "Ingresa el **nombre** de la recompensa:",
        parse_mode="Markdown",
        reply_markup=get_back_keyboard("admin_content_rewards"),
    )
    await state.set_state(AdminStates.creating_reward_name)
    await callback.answer()

@router.message(AdminStates.creating_reward_name)
async def admin_process_reward_name(message: Message, state: FSMContext):
    if message.from_user.id != Config.ADMIN_ID: return
    await state.update_data(name=message.text)
    await message.answer("Ingresa la **descripción** de la recompensa:")
    await state.set_state(AdminStates.creating_reward_description)

@router.message(AdminStates.creating_reward_description)
async def admin_process_reward_description(message: Message, state: FSMContext):
    if message.from_user.id != Config.ADMIN_ID: return
    await state.update_data(description=message.text)
    await message.answer("Ingresa el **costo** de la recompensa (solo números):")
    await state.set_state(AdminStates.creating_reward_cost)

@router.message(AdminStates.creating_reward_cost)
async def admin_process_reward_cost(message: Message, state: FSMContext):
    if message.from_user.id != Config.ADMIN_ID: return
    try:
        cost = int(message.text)
        await state.update_data(cost=cost)
        await message.answer("Ingresa el **stock** de la recompensa (-1 para ilimitado, solo números):")
        await state.set_state(AdminStates.creating_reward_stock)
    except ValueError:
        await message.answer("Costo inválido. Por favor, ingresa un número.")

@router.message(AdminStates.creating_reward_stock)
async def admin_process_reward_stock(message: Message, state: FSMContext, session: AsyncSession):
    if message.from_user.id != Config.ADMIN_ID: return
    try:
        stock = int(message.text)
        data = await state.get_data()
        reward_service = RewardService(session)
        await reward_service.create_reward(data['name'], data['description'], data['cost'], stock)
        await message.answer("✅ Recompensa creada exitosamente.", reply_markup=get_admin_main_keyboard())
        await state.clear()
    except ValueError:
        await message.answer("Stock inválido. Por favor, ingresa un número.")
    except Exception as e:
        await message.answer(f"Error al crear recompensa: `{e}`", parse_mode="Markdown")
        await state.clear()


@router.callback_query(F.data == "admin_create_mission")
async def admin_start_create_mission(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != Config.ADMIN_ID: return
    await callback.message.edit_text(
        "Ingresa el **nombre** de la misión:",
        reply_markup=get_back_keyboard("admin_content_missions"),
    )
    await state.set_state(AdminStates.creating_mission_name)
    await callback.answer()

@router.message(AdminStates.creating_mission_name)
async def admin_process_mission_name(message: Message, state: FSMContext):
    if message.from_user.id != Config.ADMIN_ID: return
    await state.update_data(name=message.text)
    await message.answer("Ingresa la **descripción** de la misión:")
    await state.set_state(AdminStates.creating_mission_description)

@router.message(AdminStates.creating_mission_description)
async def admin_process_mission_description(message: Message, state: FSMContext):
    if message.from_user.id != Config.ADMIN_ID: return
    await state.update_data(description=message.text)
    await message.answer("Ingresa los **puntos de recompensa** de la misión (solo números):")
    await state.set_state(AdminStates.creating_mission_points)

@router.message(AdminStates.creating_mission_points)
async def admin_process_mission_points(message: Message, state: FSMContext):
    if message.from_user.id != Config.ADMIN_ID: return
    try:
        points = int(message.text)
        await state.update_data(points_reward=points)
        await message.answer("Ingresa el **tipo** de misión (ej. `daily`, `weekly`, `one_time`, `event`, `reaction`):")
        await state.set_state(AdminStates.creating_mission_type)
    except ValueError:
        await message.answer("Puntos inválidos. Por favor, ingresa un número.")

@router.message(AdminStates.creating_mission_type)
async def admin_process_mission_type(message: Message, state: FSMContext, session: AsyncSession): # <-- ¡CORRECCIÓN AQUÍ!
    if message.from_user.id != Config.ADMIN_ID: return
    mission_type = message.text.lower()
    valid_types = ['daily', 'weekly', 'one_time', 'event', 'reaction']
    if mission_type not in valid_types:
        await message.answer(f"Tipo de misión inválido. Por favor, elige entre: {', '.join(valid_types)}")
        return
    await state.update_data(type=mission_type)

    if mission_type == 'reaction': # Reaction missions implicitly require action (clicking a button)
        await state.update_data(requires_action=True)
        # For reaction missions, action_data might specify which button/reaction type to look for,
        # but for now, we'll keep it simple and just mark that it requires action.
        await state.update_data(action_data={}) # No specific action_data needed for now, but keep as dict
        data = await state.get_data()
        mission_service = MissionService(session) # <-- ¡CORRECCIÓN AQUÍ!
        await mission_service.create_mission(
            data['name'], data['description'], data['points_reward'], data['type'],
            data['requires_action'], data.get('action_data')
        )
        await message.answer("✅ Misión de reacción creada exitosamente.", reply_markup=get_admin_main_keyboard())
        await state.clear()
    else: # For other mission types, ask about requires_action
        await message.answer("¿Requiere una acción externa para completarse? (Sí/No):")
        await state.set_state(AdminStates.creating_mission_requires_action)
        # handlers/admin_handlers.py - Bloque 2 de 2 (continuación)

@router.message(AdminStates.creating_mission_requires_action)
async def admin_process_mission_requires_action(message: Message, state: FSMContext, session: AsyncSession):
    if message.from_user.id != Config.ADMIN_ID: return
    requires_action_text = message.text.lower()
    requires_action = requires_action_text == 'sí' or requires_action_text == 'si'
    await state.update_data(requires_action=requires_action)

    data = await state.get_data()
    mission_service = MissionService(session)
    await mission_service.create_mission(
        data['name'], data['description'], data['points_reward'], data['type'],
        data['requires_action'], data.get('action_data')
    )
    await message.answer("✅ Misión creada exitosamente.", reply_markup=get_admin_main_keyboard())
    await state.clear()


@router.callback_query(F.data == "admin_export_data")
async def admin_export_data(callback: CallbackQuery, session: AsyncSession):
    if callback.from_user.id != Config.ADMIN_ID: return

    try:
        users_stmt = select(User)
        users_result = await session.execute(users_stmt)
        users = users_result.scalars().all()

        if not users:
            await callback.answer("No hay datos de usuarios para exportar.", show_alert=True)
            return

        output = io.StringIO()
        writer = csv.writer(output)

        # Encabezados
        writer.writerow(['ID', 'Username', 'First Name', 'Last Name', 'Points', 'Level', 'Achievements', 'Missions Completed', 'Last Daily Mission Reset', 'Last Weekly Mission Reset', 'Channel Reactions', 'Created At', 'Updated At'])

        # Datos de usuarios
        for user in users:
            writer.writerow([
                user.id,
                user.username,
                user.first_name,
                user.last_name,
                user.points,
                user.level,
                json.dumps(user.achievements), # Convertir dict a string JSON
                json.dumps(user.missions_completed), # Convertir dict a string JSON
                user.last_daily_mission_reset.isoformat() if user.last_daily_mission_reset else '',
                user.last_weekly_mission_reset.isoformat() if user.last_weekly_mission_reset else '',
                json.dumps(user.channel_reactions) if user.channel_reactions else '{}', # Nuevo campo
                user.created_at.isoformat() if user.created_at else '',
                user.updated_at.isoformat() if user.updated_at else ''
            ])

        output.seek(0)
        await callback.message.answer_document(InputFile(io.BytesIO(output.getvalue().encode('utf-8')), filename="users_data.csv"))
        await callback.answer("Datos exportados exitosamente.", show_alert=True)
    except Exception as e:
        logger.error(f"Error exporting data: {e}")
        await callback.answer(f"Error al exportar datos: {e}", show_alert=True)


@router.callback_query(F.data == "admin_reset_season")
async def admin_confirm_reset_season(callback: CallbackQuery):
    if callback.from_user.id != Config.ADMIN_ID: return
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Confirmar Reseteo (¡IRREVERSIBLE!)", callback_data="admin_perform_reset_season")],
        [InlineKeyboardButton(text="❌ Cancelar", callback_data="admin_cancel_reset_season")]
    ])
    await callback.message.edit_text("⚠️ **Advertencia: Esto reseteará todos los puntos y logros de TODOS los usuarios.**\n\n¿Estás seguro?", reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "admin_perform_reset_season")
async def admin_perform_reset_season(callback: CallbackQuery, session: AsyncSession):
    if callback.from_user.id != Config.ADMIN_ID: return
    try:
        stmt = update(User).values(points=0, level=1, achievements={}, missions_completed={}, channel_reactions={}) # Reset channel_reactions too
        await session.execute(stmt)
        await session.commit()
        await callback.message.edit_text("✅ ¡Temporada reseteada exitosamente! Todos los puntos, niveles, logros y misiones completadas han sido reiniciados.")
        await callback.answer()
    except Exception as e:
        await callback.message.edit_text(f"❌ Error al resetear la temporada: {e}")
        await callback.answer()

@router.callback_query(F.data == "admin_cancel_reset_season")
async def admin_cancel_reset_season(callback: CallbackQuery):
    if callback.from_user.id != Config.ADMIN_ID: return
    await callback.message.edit_text("Reseteo de temporada cancelado.", reply_markup=get_admin_main_keyboard())
    await callback.answer()

@router.callback_query(F.data == "admin_assign_points")
async def admin_start_assign_points(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != Config.ADMIN_ID: return
    await callback.message.edit_text(
        "Ingresa el ID de usuario o el username (con @) al que quieres asignar puntos:",
        reply_markup=get_back_keyboard("admin_manage_users"),
    )
    await state.update_data(points_operation="generic")
    await state.set_state(AdminStates.assigning_points_target)
    await callback.answer()

@router.message(AdminStates.assigning_points_target)
async def admin_process_assign_points_target(message: Message, state: FSMContext):
    if message.from_user.id != Config.ADMIN_ID: return
    target_user_identifier = message.text.strip()
    data = await state.get_data()
    operation = data.get("points_operation", "generic")
    await state.update_data(target_user_identifier=target_user_identifier)

    if operation == "add":
        prompt = f"Ingresa la cantidad de puntos a **sumar** a `{target_user_identifier}`:"
    elif operation == "deduct":
        prompt = f"Ingresa la cantidad de puntos a **restar** a `{target_user_identifier}`:"
    else:
        prompt = f"Ingresa la cantidad de puntos a asignar a `{target_user_identifier}` (puede ser negativo para restar):"

    await message.answer(prompt, parse_mode="Markdown")
    await state.set_state(AdminStates.assigning_points_amount)

@router.message(AdminStates.assigning_points_amount)
async def admin_process_assign_points_amount(message: Message, state: FSMContext, session: AsyncSession):
    if message.from_user.id != Config.ADMIN_ID: return
    try:
        points_to_add = int(message.text)
        data = await state.get_data()
        user_identifier = data['target_user_identifier']
        operation = data.get('points_operation', 'generic')

        user = None
        if user_identifier.isdigit(): # Try to find by ID
            user = await session.get(User, int(user_identifier))
        elif user_identifier.startswith('@'): # Try to find by username
            stmt = select(User).where(User.username == user_identifier[1:])
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

        if not user:
            await message.answer("Usuario no encontrado. Asegúrate de que el ID/username sea correcto y que el usuario haya interactuado con el bot al menos una vez.")
            await state.clear()
            return

        point_service = PointService(session)
        if operation == 'deduct':
            updated_user = await point_service.deduct_points(user.id, points_to_add)
            if updated_user:
                await message.answer(
                    f"✅ Se han restado `{points_to_add}` puntos a `{updated_user.first_name or updated_user.username}`. Ahora tiene `{updated_user.points}` puntos.",
                    parse_mode="Markdown",
                )
            else:
                await message.answer("No se pudo restar puntos (quizás el usuario no tiene suficientes).")
        else:
            updated_user = await point_service.add_points(user.id, points_to_add)
            await message.answer(
                f"✅ Se han sumado `{points_to_add}` puntos a `{updated_user.first_name or updated_user.username}`. Ahora tiene `{updated_user.points}` puntos.",
                parse_mode="Markdown",
            )
        await state.clear()
    except ValueError:
        await message.answer("Cantidad de puntos inválida. Por favor, ingresa un número.")
    except Exception as e:
        await message.answer(f"Error al asignar puntos: `{e}`", parse_mode="Markdown")
        await state.clear()


@router.callback_query(F.data == "admin_activate_event")
async def admin_start_activate_event(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != Config.ADMIN_ID: return
    await callback.message.edit_text(
        "Ingresa el **nombre** del evento:",
        reply_markup=get_back_keyboard("admin_main_menu"),
    )
    await state.set_state(AdminStates.activating_event_name)
    await callback.answer()

@router.message(AdminStates.activating_event_name)
async def admin_process_event_name(message: Message, state: FSMContext):
    if message.from_user.id != Config.ADMIN_ID: return
    await state.update_data(name=message.text)
    await message.answer("Ingresa la **descripción** del evento:")
    await state.set_state(AdminStates.activating_event_description)

@router.message(AdminStates.activating_event_description)
async def admin_process_event_description(message: Message, state: FSMContext):
    if message.from_user.id != Config.ADMIN_ID: return
    await state.update_data(description=message.text)
    await message.answer("Ingresa el **multiplicador** de puntos del evento (ej. 2 para doble puntos, solo números):")
    await state.set_state(AdminStates.activating_event_multiplier)

@router.message(AdminStates.activating_event_multiplier)
async def admin_process_event_multiplier(message: Message, state: FSMContext):
    if message.from_user.id != Config.ADMIN_ID: return
    try:
        multiplier = int(message.text)
        if multiplier < 1:
            await message.answer("El multiplicador debe ser al menos 1.")
            return
        await state.update_data(multiplier=multiplier)
        await message.answer("Ingresa la **duración** del evento en horas (0 para indefinido):")
        await state.set_state(AdminStates.activating_event_duration)
    except ValueError:
        await message.answer("Multiplicador inválido. Por favor, ingresa un número.")

@router.message(AdminStates.activating_event_duration)
async def admin_process_event_duration(message: Message, state: FSMContext, session: AsyncSession):
    if message.from_user.id != Config.ADMIN_ID: return
    try:
        duration_hours = int(message.text)
        data = await state.get_data()

        start_time = datetime.datetime.now()
        end_time = None
        if duration_hours > 0:
            end_time = start_time + datetime.timedelta(hours=duration_hours)

        new_event = Event(
            name=data['name'],
            description=data['description'],
            multiplier=data['multiplier'],
            is_active=True,
            start_time=start_time,
            end_time=end_time
        )
        session.add(new_event)
        await session.commit()
        await session.refresh(new_event)

        # Notificar a los usuarios en el canal principal sobre el evento
        event_message = (
            f"📢 **¡Nuevo Evento Activo: {new_event.name}!**\n\n"
            f"{new_event.description}\n\n"
            f"Todos los puntos ganados se multiplicarán por **{new_event.multiplier}x**.\n"
        )
        if new_event.end_time:
            event_message += f"¡El evento finalizará el `{new_event.end_time.strftime('%d/%m/%Y %H:%M')}`!"
        else:
            event_message += "¡Este evento es indefinido!"

        # Enviar al canal
        await message.bot.send_message(Config.CHANNEL_ID, event_message, parse_mode="Markdown")

        await message.answer("✅ Evento activado y publicado en el canal exitosamente.", reply_markup=get_admin_main_keyboard())
        await state.clear()
    except ValueError:
        await message.answer("Duración inválida. Por favor, ingresa un número de horas.")
    except Exception as e:
        logger.error(f"Error activating event: {e}")
        await message.answer(f"Error al activar evento: `{e}`", parse_mode="Markdown")
        await state.clear()


# ¡NUEVOS HANDLERS para enviar mensajes al canal con botones de reacción!
@router.callback_query(F.data == "admin_send_channel_post_reactions")
async def admin_start_channel_post_reactions(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != Config.ADMIN_ID: return
    await callback.message.edit_text(
        "Por favor, envía el **texto del mensaje** que quieres publicar en el canal. "
        "Este mensaje tendrá los botones de reacción configurados debajo.",
        parse_mode="Markdown",
        reply_markup=get_back_keyboard("admin_main_menu"),
    )
    await state.set_state(AdminStates.waiting_for_channel_post_text)
    await callback.answer()

@router.message(AdminStates.waiting_for_channel_post_text)
async def admin_process_channel_post_text(message: Message, state: FSMContext, bot: Bot):
    if message.from_user.id != Config.ADMIN_ID: return
    
    post_text = message.text
    
    try:
        # Enviar el mensaje al canal
        sent_message = await bot.send_message(
            chat_id=Config.CHANNEL_ID,
            text=post_text,
            reply_markup=get_reaction_keyboard(message_id=0), # message_id temporal, lo actualizaremos
            parse_mode="Markdown"
        )
        
        # Una vez enviado, obtenemos el message_id real del mensaje en el canal
        real_message_id = sent_message.message_id
        
        # Ahora, editamos el mensaje para poner el message_id correcto en el callback_data
        # Esto es crucial porque el message_id no se sabe hasta que el mensaje es enviado.
        updated_keyboard = get_reaction_keyboard(message_id=real_message_id)
        await bot.edit_message_reply_markup(
            chat_id=Config.CHANNEL_ID,
            message_id=real_message_id,
            reply_markup=updated_keyboard
        )

        await message.answer(
            f"✅ Mensaje publicado en el canal (ID: `{real_message_id}`) con botones de reacción. "
            "Los usuarios ahora pueden reaccionar a él para ganar puntos.",
            reply_markup=get_admin_main_keyboard(),
            parse_mode="Markdown"
        )
        logger.info(f"Admin {message.from_user.id} posted message {real_message_id} to channel {Config.CHANNEL_ID} with reaction buttons.")
        await state.clear()

    except Exception as e:
        logger.error(f"Error sending channel post with reactions: {e}")
        await message.answer(f"❌ Error al publicar el mensaje en el canal: `{e}`", reply_markup=get_admin_main_keyboard(), parse_mode="Markdown")
        await state.clear()
            
