import logging
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.fsm.context import FSMContext

from database.models import User, Mission, Reward, Event
from services.point_service import add_points, can_receive_points, add_points_by_admin
from services.level_service import get_level_by_points, get_progress_to_next_level
from services.achievement_service import check_and_award_achievements

from utils.keyboard_utils import get_admin_menu_keyboard, get_missions_keyboard, get_rewards_keyboard
from utils.message_utils import send_admin_log, send_progress_bar, send_achievements_gallery
from utils.messages import ADMIN_WELCOME_MESSAGE, POINTS_LIMIT_MESSAGE

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import datetime

router = Router()

logger = logging.getLogger(__name__)

# --- FUNCIONES AUXILIARES ---
async def get_or_create_user(session: AsyncSession, telegram_id, username=None):
    result = await session.execute(
        select(User).where(User.telegram_id == str(telegram_id))
    )
    user = result.scalar()
    if not user:
        user = User(
            telegram_id=str(telegram_id),
            username=username,
            joined_at=datetime.datetime.now(),
            last_active=datetime.datetime.now(),
            points=0,
            level="Suscriptor Íntimo",
            is_admin=True
        )
        session.add(user)
        await session.commit()
    return user

# --- HANDLERS DE ADMIN ---

@router.message(Command("admin"))
async def cmd_admin_panel(message: Message, state: FSMContext, session: AsyncSession):
    user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
    if not user.is_admin:
        await message.answer("No tienes permisos para este comando.")
        return
    await message.answer(
        ADMIN_WELCOME_MESSAGE,
        reply_markup=get_admin_menu_keyboard()
    )

@router.message(Command("sumarpuntos"))
async def cmd_sumarpuntos(message: Message, session: AsyncSession):
    user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
    if not user.is_admin:
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

    ok, msg = await add_points_by_admin(session, target_user.id, puntos, description="Admin manual")
    if ok:
        await message.answer(f"Se sumaron {puntos} puntos a {target_user.username or target_user.telegram_id}.")
        await send_admin_log(session, user, f"Sumó {puntos} puntos a {target_user.username or target_user.telegram_id}")
    else:
        await message.answer(f"Error: {msg}")

@router.message(Command("restapuntos"))
async def cmd_restapuntos(message: Message, session: AsyncSession):
    user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
    if not user.is_admin:
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

    target_user.points -= puntos
    await session.commit()
    await message.answer(f"Se restaron {puntos} puntos a {target_user.username or target_user.telegram_id}.")
    await send_admin_log(session, user, f"Restó {puntos} puntos a {target_user.username or target_user.telegram_id}")

@router.message(Command("forzarnivel"))
async def cmd_forzarnivel(message: Message, session: AsyncSession):
    user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
    if not user.is_admin:
        await message.answer("No tienes permisos para este comando.")
        return
    try:
        # /forzarnivel <telegram_id> <nivel>
        _, target_id, nuevo_nivel = message.text.split(maxsplit=2)
        target_user = await get_or_create_user(session, target_id)
        target_user.level = nuevo_nivel
        await session.commit()
    except Exception:
        await message.answer("Uso: /forzarnivel <telegram_id> <nivel>")
        return
    await message.answer(f"Nivel de {target_user.username or target_user.telegram_id} actualizado a {nuevo_nivel}.")
    await send_admin_log(session, user, f"Forzó nivel {nuevo_nivel} a {target_user.username or target_user.telegram_id}")

# --- Handler para crear misiones ---
@router.message(Command("crearmision"))
async def cmd_crearmision(message: Message, session: AsyncSession):
    user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
    if not user.is_admin:
        await message.answer("No tienes permisos para este comando.")
        return
    # /crearmision <nombre>;<descripcion>;<tipo>
    try:
        _, datos = message.text.split(maxsplit=1)
        nombre, descripcion, tipo = datos.split(";")
        mission = Mission(
            name=nombre.strip(),
            description=descripcion.strip(),
            type=tipo.strip(),
            start_time=datetime.datetime.now(),
            is_active=True
        )
        session.add(mission)
        await session.commit()
    except Exception:
        await message.answer("Uso: /crearmision <nombre>;<descripcion>;<tipo>")
        return
    await message.answer(f"Misión '{nombre}' creada y activada.")
    await send_admin_log(session, user, f"Creó misión {nombre}")

# --- Handler para activar/desactivar misiones ---
@router.message(Command("activarmision"))
async def cmd_activarmision(message: Message, session: AsyncSession):
    user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
    if not user.is_admin:
        await message.answer("No tienes permisos para este comando.")
        return
    try:
        # /activarmision <id> <on/off>
        _, mission_id, action = message.text.split()
        mission = await session.get(Mission, int(mission_id))
        if not mission:
            await message.answer("Misión no encontrada.")
            return
        if action.lower() == "on":
            mission.is_active = True
        elif action.lower() == "off":
            mission.is_active = False
        else:
            await message.answer("Acción inválida. Usa on/off.")
            return
        await session.commit()
    except Exception:
        await message.answer("Uso: /activarmision <id> <on/off>")
        return
    await message.answer(f"Misión {mission.name} ahora {'activa' if mission.is_active else 'inactiva'}.")
    await send_admin_log(session, user, f"Cambió estado de misión {mission.name} a {action}")

# Más funciones y handlers admin aquí abajo...

# (continúa en la siguiente parte)
# --- Handler para crear recompensas ---
@router.message(Command("crearrecompensa"))
async def cmd_crearrecompensa(message: Message, session: AsyncSession):
    user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
    if not user.is_admin:
        await message.answer("No tienes permisos para este comando.")
        return
    # /crearrecompensa <nombre>;<descripcion>;<costo>
    try:
        _, datos = message.text.split(maxsplit=1)
        nombre, descripcion, costo = datos.split(";")
        reward = Reward(
            name=nombre.strip(),
            description=descripcion.strip(),
            cost_in_points=int(costo.strip()),
            is_active=True
        )
        session.add(reward)
        await session.commit()
    except Exception:
        await message.answer("Uso: /crearrecompensa <nombre>;<descripcion>;<costo>")
        return
    await message.answer(f"Recompensa '{nombre}' creada y activada.")
    await send_admin_log(session, user, f"Creó recompensa {nombre}")

# --- Handler para activar/desactivar recompensas ---
@router.message(Command("activarrecompensa"))
async def cmd_activarrecompensa(message: Message, session: AsyncSession):
    user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
    if not user.is_admin:
        await message.answer("No tienes permisos para este comando.")
        return
    try:
        # /activarrecompensa <id> <on/off>
        _, reward_id, action = message.text.split()
        reward = await session.get(Reward, int(reward_id))
        if not reward:
            await message.answer("Recompensa no encontrada.")
            return
        if action.lower() == "on":
            reward.is_active = True
        elif action.lower() == "off":
            reward.is_active = False
        else:
            await message.answer("Acción inválida. Usa on/off.")
            return
        await session.commit()
    except Exception:
        await message.answer("Uso: /activarrecompensa <id> <on/off>")
        return
    await message.answer(f"Recompensa {reward.name} ahora {'activa' if reward.is_active else 'inactiva'}.")
    await send_admin_log(session, user, f"Cambió estado de recompensa {reward.name} a {action}")

# --- Handler para eventos (crear/activar/desactivar) ---
@router.message(Command("crearevento"))
async def cmd_crearevento(message: Message, session: AsyncSession):
    user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
    if not user.is_admin:
        await message.answer("No tienes permisos para este comando.")
        return
    # /crearevento <nombre>;<descripcion>;<start>;<end>
    try:
        _, datos = message.text.split(maxsplit=1)
        nombre, descripcion, start_str, end_str = datos.split(";")
        start_time = datetime.datetime.fromisoformat(start_str.strip())
        end_time = datetime.datetime.fromisoformat(end_str.strip())
        from database.models import Event
        evento = Event(
            name=nombre.strip(),
            description=descripcion.strip(),
            start_time=start_time,
            end_time=end_time,
            is_active=True
        )
        session.add(evento)
        await session.commit()
    except Exception:
        await message.answer("Uso: /crearevento <nombre>;<descripcion>;<start>;<end> (formato: YYYY-MM-DDTHH:MM:SS)")
        return
    await message.answer(f"Evento '{nombre}' creado y activado.")
    await send_admin_log(session, user, f"Creó evento {nombre}")

@router.message(Command("activarevento"))
async def cmd_activarevento(message: Message, session: AsyncSession):
    user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
    if not user.is_admin:
        await message.answer("No tienes permisos para este comando.")
        return
    try:
        # /activarevento <id> <on/off>
        from database.models import Event
        _, event_id, action = message.text.split()
        event = await session.get(Event, int(event_id))
        if not event:
            await message.answer("Evento no encontrado.")
            return
        if action.lower() == "on":
            event.is_active = True
        elif action.lower() == "off":
            event.is_active = False
        else:
            await message.answer("Acción inválida. Usa on/off.")
            return
        await session.commit()
    except Exception:
        await message.answer("Uso: /activarevento <id> <on/off>")
        return
    await message.answer(f"Evento {event.name} ahora {'activo' if event.is_active else 'inactivo'}.")
    await send_admin_log(session, user, f"Cambió estado de evento {event.name} a {action}")

# --- Otros handlers admin, según tu lógica original ---
# Puedes colocar aquí cualquier otro comando admin personalizado
# Asegúrate que los imports y uso de servicios estén alineados a la arquitectura nueva

# --- Fin del archivo ---
