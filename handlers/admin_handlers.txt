import json
import csv
import io
import datetime

from aiogram import Router, F
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
from utils.keyboard_utils import get_admin_main_keyboard, get_main_menu_keyboard
from config import Config

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

    assigning_points_user = State()
    assigning_points_amount = State()

# Middleware to check if user is admin (simplified for this example)
@router.message(Command("admin"))
@router.callback_query(F.data.startswith("admin_"))
async def admin_panel(union: Message | CallbackQuery):
    user_id = union.from_user.id
    if user_id != Config.ADMIN_ID:
        if isinstance(union, Message):
            await union.answer("No tienes permisos de administrador.")
        elif isinstance(union, CallbackQuery):
            await union.answer("No tienes permisos de administrador.", show_alert=True)
        return

    if isinstance(union, Message):
        await union.answer("Panel de Administración:", reply_markup=get_admin_main_keyboard(), parse_mode="Markdown")
    elif isinstance(union, CallbackQuery):
        await union.message.edit_text("Panel de Administración:", reply_markup=get_admin_main_keyboard(), parse_mode="Markdown")
        await union.answer()

# --- Admin: Create Reward ---
@router.callback_query(F.data == "admin_create_reward")
async def admin_create_reward_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Ingresa el nombre de la nueva recompensa:")
    await state.set_state(AdminStates.creating_reward_name)
    await callback.answer()

@router.message(AdminStates.creating_reward_name)
async def admin_create_reward_name(message: Message, state: FSMContext):
    if message.from_user.id != Config.ADMIN_ID: return
    await state.update_data(name=message.text)
    await message.answer("Ingresa la descripción de la recompensa:")
    await state.set_state(AdminStates.creating_reward_description)

@router.message(AdminStates.creating_reward_description)
async def admin_create_reward_description(message: Message, state: FSMContext):
    if message.from_user.id != Config.ADMIN_ID: return
    await state.update_data(description=message.text)
    await message.answer("Ingresa el costo en puntos de la recompensa (solo números):")
    await state.set_state(AdminStates.creating_reward_cost)

@router.message(AdminStates.creating_reward_cost)
async def admin_create_reward_cost(message: Message, state: FSMContext):
    if message.from_user.id != Config.ADMIN_ID: return
    try:
        cost = int(message.text)
        await state.update_data(cost=cost)
        await message.answer("Ingresa el stock de la recompensa (ej. 10, o -1 para ilimitado):")
        await state.set_state(AdminStates.creating_reward_stock)
    except ValueError:
        await message.answer("Costo inválido. Por favor, ingresa un número.")

@router.message(AdminStates.creating_reward_stock)
async def admin_create_reward_stock(message: Message, state: FSMContext, session: AsyncSession):
    if message.from_user.id != Config.ADMIN_ID: return
    try:
        stock = int(message.text)
        data = await state.get_data()
        reward_service = RewardService(session)
        await reward_service.create_reward(data['name'], data['description'], data['cost'], stock)
        await message.answer("✅ Recompensa creada exitosamente.", reply_markup=get_admin_main_keyboard(), parse_mode="Markdown")
        await state.clear()
    except ValueError:
        await message.answer("Stock inválido. Por favor, ingresa un número.")
    except Exception as e:
        await message.answer(f"Error al crear recompensa: `{e}`", reply_markup=get_admin_main_keyboard(), parse_mode="Markdown")
        await state.clear()

# --- Admin: Create Mission ---
@router.callback_query(F.data == "admin_create_mission")
async def admin_create_mission_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Ingresa el nombre de la nueva misión:")
    await state.set_state(AdminStates.creating_mission_name)
    await callback.answer()

@router.message(AdminStates.creating_mission_name)
async def admin_create_mission_name(message: Message, state: FSMContext):
    if message.from_user.id != Config.ADMIN_ID: return
    await state.update_data(name=message.text)
    await message.answer("Ingresa la descripción de la misión:")
    await state.set_state(AdminStates.creating_mission_description)

@router.message(AdminStates.creating_mission_description)
async def admin_create_mission_description(message: Message, state: FSMContext):
    if message.from_user.id != Config.ADMIN_ID: return
    await state.update_data(description=message.text)
    await message.answer("Ingresa los puntos de recompensa de la misión (solo números):")
    await state.set_state(AdminStates.creating_mission_points)

@router.message(AdminStates.creating_mission_points)
async def admin_create_mission_points(message: Message, state: FSMContext):
    if message.from_user.id != Config.ADMIN_ID: return
    try:
        points = int(message.text)
        await state.update_data(points_reward=points)
        await message.answer("Ingresa el tipo de misión (daily, weekly, one_time):")
        await state.set_state(AdminStates.creating_mission_type)
    except ValueError:
        await message.answer("Puntos inválidos. Por favor, ingresa un número.")

@router.message(AdminStates.creating_mission_type)
async def admin_create_mission_type(message: Message, state: FSMContext):
    if message.from_user.id != Config.ADMIN_ID: return
    mission_type = message.text.lower()
    if mission_type not in ["daily", "weekly", "one_time"]:
        await message.answer("Tipo de misión inválido. Por favor, usa 'daily', 'weekly' o 'one_time'.")
        return
    await state.update_data(type=mission_type)
    await message.answer("¿Requiere una acción específica (ej. clic en un botón)? (Sí/No):")
    await state.set_state(AdminStates.creating_mission_requires_action)
@router.message(AdminStates.creating_mission_requires_action)
async def admin_create_mission_requires_action(message: Message, state: FSMContext, session: AsyncSession):
    if message.from_user.id != Config.ADMIN_ID: return
    requires_action = message.text.lower() == "sí" or message.text.lower() == "si"
    await state.update_data(requires_action=requires_action)
    if requires_action:
        await message.answer("Ingresa los datos de la acción (ej. `{'button_id': 'unique_button_id'}` en formato JSON):", parse_mode="Markdown")
        await state.set_state(AdminStates.creating_mission_action_data)
    else:
        data = await state.get_data()
        mission_service = MissionService(session)
        try:
            await mission_service.create_mission(
                data['name'], data['description'], data['points_reward'],
                data['type'], data['requires_action'], None
            )
            await message.answer("✅ Misión creada exitosamente.", reply_markup=get_admin_main_keyboard(), parse_mode="Markdown")
            await state.clear()
        except Exception as e:
            await message.answer(f"Error al crear misión: `{e}`", reply_markup=get_admin_main_keyboard(), parse_mode="Markdown")
            await state.clear()

@router.message(AdminStates.creating_mission_action_data)
async def admin_create_mission_action_data(message: Message, state: FSMContext, session: AsyncSession):
    if message.from_user.id != Config.ADMIN_ID: return
    try:
        action_data = json.loads(message.text)
        data = await state.get_data()
        mission_service = MissionService(session)
        await mission_service.create_mission(
            data['name'], data['description'], data['points_reward'],
            data['type'], data['requires_action'], action_data
        )
        await message.answer("✅ Misión creada exitosamente.", reply_markup=get_admin_main_keyboard(), parse_mode="Markdown")
        await state.clear()
    except json.JSONDecodeError:
        await message.answer("Formato JSON inválido. Inténtalo de nuevo.")
    except Exception as e:
        await message.answer(f"Error al crear misión: `{e}`", reply_markup=get_admin_main_keyboard(), parse_mode="Markdown")
        await state.clear()

# --- Admin: Activate Event ---
@router.callback_query(F.data == "admin_activate_event")
async def admin_activate_event_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Ingresa el nombre del evento:")
    await state.set_state(AdminStates.activating_event_name)
    await callback.answer()

@router.message(AdminStates.activating_event_name)
async def admin_activate_event_name(message: Message, state: FSMContext):
    if message.from_user.id != Config.ADMIN_ID: return
    await state.update_data(name=message.text)
    await message.answer("Ingresa la descripción del evento:")
    await state.set_state(AdminStates.activating_event_description)

@router.message(AdminStates.activating_event_description)
async def admin_activate_event_description(message: Message, state: FSMContext):
    if message.from_user.id != Config.ADMIN_ID: return
    await state.update_data(description=message.text)
    await message.answer("Ingresa el multiplicador de puntos (ej. 2 para doble puntos):")
    await state.set_state(AdminStates.activating_event_multiplier)

@router.message(AdminStates.activating_event_multiplier)
async def admin_activate_event_multiplier(message: Message, state: FSMContext):
    if message.from_user.id != Config.ADMIN_ID: return
    try:
        multiplier = int(message.text)
        await state.update_data(multiplier=multiplier)
        await message.answer("Ingresa la duración del evento en horas (ej. 24 para 1 día, 0 para indefinido):")
        await state.set_state(AdminStates.activating_event_duration)
    except ValueError:
        await message.answer("Multiplicador inválido. Por favor, ingresa un número.")

@router.message(AdminStates.activating_event_duration)
async def admin_activate_event_duration(message: Message, state: FSMContext, session: AsyncSession, bot):
    if message.from_user.id != Config.ADMIN_ID: return
    try:
        duration_hours = int(message.text)
        data = await state.get_data()
        start_time = datetime.datetime.now()
        end_time = start_time + datetime.timedelta(hours=duration_hours) if duration_hours > 0 else None

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

        await message.answer("✅ Evento activado exitosamente.", reply_markup=get_admin_main_keyboard(), parse_mode="Markdown")
        await state.clear()

        # Notify in channel
        duration_text = f"Finaliza en: {duration_hours} horas." if duration_hours > 0 else "Duración: Indefinida."
        await bot.send_message(Config.CHANNEL_ID,
                               f"📢 **¡Evento Especial Activado!**\n\n"
                               f"✨ **{new_event.name}**\n"
                               f"{new_event.description}\n\n"
                               f"¡Gana **{new_event.multiplier}x puntos** durante este evento!\n"
                               f"{duration_text}",
                               parse_mode="Markdown")
    except ValueError:
        await message.answer("Duración inválida. Por favor, ingresa un número de horas.")
    except Exception as e:
        await message.answer(f"Error al activar evento: `{e}`", reply_markup=get_admin_main_keyboard(), parse_mode="Markdown")
        await state.clear()

# --- Admin: Export Data ---
@router.callback_query(F.data == "admin_export_data")
async def admin_export_data(callback: CallbackQuery, session: AsyncSession):
    if callback.from_user.id != Config.ADMIN_ID:
        await callback.answer("No tienes permisos de administrador.", show_alert=True)
        return

    stmt = select(User)
    result = await session.execute(stmt)
    users = result.scalars().all()

    if not users:
        await callback.answer("No hay datos de usuarios para exportar.", show_alert=True)
        return

    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow(['ID', 'Username', 'First Name', 'Last Name', 'Points', 'Level', 'Achievements', 'Missions Completed', 'Created At'])

    # Write data
    for user in users:
        writer.writerow([
            user.id,
            user.username,
            user.first_name,
            user.last_name,
            user.points,
            user.level,
            json.dumps(user.achievements), # JSON as string
            json.dumps(user.missions_completed), # JSON as string
            user.created_at.isoformat()
        ])

    output.seek(0)
    await callback.message.answer_document(
        document=InputFile(io.BytesIO(output.getvalue().encode('utf-8')), filename="gamification_data.csv"),
        caption="Aquí están los datos de usuarios."
    )
    await callback.answer("Exportando datos...", show_alert=True)

# --- Admin: Reset Season ---
@router.callback_query(F.data == "admin_reset_season")
async def admin_reset_season_confirm(callback: CallbackQuery):
    if callback.from_user.id != Config.ADMIN_ID:
        await callback.answer("No tienes permisos de administrador.", show_alert=True)
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Confirmar Reseteo", callback_data="admin_confirm_reset_season")],
        [InlineKeyboardButton(text="❌ Cancelar", callback_data="admin_panel")]
    ])
    await callback.message.edit_text(
        "⚠️ **¡Advertencia!** Esto reseteará los puntos y niveles de todos los usuarios. "
        "Se guardará un historial de los ganadores de la temporada. ¿Estás seguro?",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == "admin_confirm_reset_season")
async def admin_reset_season(callback: CallbackQuery, session: AsyncSession, bot):
    if callback.from_user.id != Config.ADMIN_ID:
        await callback.answer("No tienes permisos de administrador.", show_alert=True)
        return

    # Get top users before reset for announcement
    stmt = select(User).order_by(User.points.desc()).limit(10)
    result = await session.execute(stmt)
    top_users_before_reset = result.scalars().all()

    # Announce winners in channel
    winners_text = "🎉 **¡Fin de Temporada de Gamificación!** 🎉\n\n"
    winners_text += "¡Felicidades a nuestros jugadores más destacados!\n\n"
    if top_users_before_reset:
        for i, user in enumerate(top_users_before_reset):
            winners_text += f"{i+1}. {user.first_name or user.username} - {user.points} puntos (Nivel {user.level})\n"
    else:
        winners_text += "No hubo participantes destacados esta temporada."

    await bot.send_message(Config.CHANNEL_ID, winners_text, parse_mode="Markdown")

    # Reset points and levels for all users
    # Clear missions_completed and reset last mission timestamps
    await session.execute(
        update(User).values(
            points=0,
            level=1,
            missions_completed={},
            last_daily_mission_reset=datetime.datetime.now(),
            last_weekly_mission_reset=datetime.datetime.now()
        )
    )
    await session.commit()

    await callback.message.edit_text("✅ Puntos y niveles reseteados exitosamente. Se ha anunciado el final de temporada.", reply_markup=get_admin_main_keyboard(), parse_mode="Markdown")
    await callback.answer()

# --- Admin: Assign Points ---
@router.message(Command("asignar_puntos"))
async def assign_points_start(message: Message, state: FSMContext):
    if message.from_user.id != Config.ADMIN_ID:
        await message.answer("No tienes permisos de administrador.")
        return
    await message.answer("Por favor, envía el ID de usuario o username de Telegram al que quieres asignar puntos.")
    await state.set_state(AdminStates.assigning_points_user)

@router.message(AdminStates.assigning_points_user)
async def assign_points_user_input(message: Message, state: FSMContext):
    if message.from_user.id != Config.ADMIN_ID: return
    user_identifier = message.text.strip()
    await state.update_data(target_user_identifier=user_identifier)
    await message.answer(f"¿Cuántos puntos quieres asignar a `{user_identifier}`? (usa números, ej. 50)", parse_mode="Markdown")
    await state.set_state(AdminStates.assigning_points_amount)

@router.message(AdminStates.assigning_points_amount)
async def assign_points_amount_input(message: Message, state: FSMContext, session: AsyncSession):
    if message.from_user.id != Config.ADMIN_ID: return
    try:
        points_to_add = int(message.text)
        data = await state.get_data()
        user_identifier = data['target_user_identifier']

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
        updated_user = await point_service.add_points(user.id, points_to_add)
        await message.answer(f"✅ Se han asignado `{points_to_add}` puntos a `{updated_user.first_name or updated_user.username}`. Ahora tiene `{updated_user.points}` puntos.", parse_mode="Markdown")
        await state.clear()
    except ValueError:
        await message.answer("Cantidad de puntos inválida. Por favor, ingresa un número.")
    except Exception as e:
        await message.answer(f"Error al asignar puntos: `{e}`", parse_mode="Markdown")
    finally:
        await state.clear()
