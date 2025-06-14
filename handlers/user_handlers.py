from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
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
    get_reaction_keyboard, get_admin_main_keyboard,
    get_root_menu, get_parent_menu, get_child_menu,  # <--- Estas fueron añadidas/confirmadas
    get_main_reply_keyboard  # <--- Asegúrate de que esta esté aquí también
)
from utils.message_utils import get_profile_message, get_mission_details_message, get_reward_details_message, get_ranking_message # Añadido get_ranking_message
from utils.messages import BOT_MESSAGES # <--- Asegúrate de que esta esté importada

from config import Config
import asyncio
import logging

logger = logging.getLogger(__name__)

router = Router()


async def _handle_start_flow(message: Message, session: AsyncSession, bot: Bot) -> None:
    """Common logic for /start handling once user is identified."""
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name

    user = await session.get(User, user_id)
    is_new_user = False

    if not user:
        new_user = User(
            id=user_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            points=0,
            level=1,
        )
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        user = new_user
        is_new_user = True
        logger.info(f"New user registered: {user_id} - {username}")
    else:
        logger.info(f"Returning user: {user_id} - {username}")

    if user_id == Config.ADMIN_ID:
        await message.answer(
            "Bienvenido al panel de administración, Diana.",
            reply_markup=get_admin_main_keyboard(),
        )
    else:
        try:
            member = await bot.get_chat_member(Config.CHANNEL_ID, user_id)
            is_member = member.status in {"member", "administrator", "creator"}
        except Exception:
            is_member = False

        if not is_member:
            await message.answer(
                "Debes unirte al canal para utilizar el bot.",
            )
            return

        await message.answer(
            BOT_MESSAGES["start_welcome_returning_user"]
            if not is_new_user
            else BOT_MESSAGES["start_welcome_new_user"],
            reply_markup=get_main_reply_keyboard(),
        )

    await set_user_menu_state(session, user_id, "root")

@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession, bot: Bot):
    """Handle /start command."""
    await _handle_start_flow(message, session, bot)


# Handler para el botón de "Menú Principal" (callback_data)
@router.callback_query(F.data == "menu_principal")
async def go_to_main_menu_from_inline(callback: CallbackQuery, session: AsyncSession):
    user_id = callback.from_user.id
    await set_user_menu_state(session, user_id, "root")
    await callback.message.edit_text(
        BOT_MESSAGES["start_welcome_returning_user"], # Mensaje consistente al volver al menú principal
        reply_markup=get_main_menu_keyboard() # Teclado inline principal
    )
    await callback.answer()

# Handler genérico para callbacks de menú (profile, missions, rewards, ranking, back)
@router.callback_query(F.data.startswith("menu:"))
async def menu_callback_handler(callback: CallbackQuery, session: AsyncSession):
    user_id = callback.from_user.id
    data = callback.data.split(':')
    menu_type = data[1]

    current_state = await get_user_menu_state(session, user_id)
    new_state = current_state # Por defecto, no cambia el estado si no hay una navegación clara

    keyboard = None
    message_text = ""

    if menu_type == "profile":
        user = await session.get(User, user_id)
        point_service = PointService(session)
        level_service = LevelService(session)
        achievement_service = AchievementService(session)
        mission_service = MissionService(session)
        active_missions = await mission_service.get_active_missions(user_id=user_id) # Pasa el user_id para filtrar misiones
        
        message_text = await get_profile_message(user, active_missions)
        keyboard = get_profile_keyboard()
        new_state = "profile"
    elif menu_type == "missions":
        mission_service = MissionService(session)
        active_missions = await mission_service.get_active_missions(user_id=user_id)
        message_text = BOT_MESSAGES["menu_missions_text"]
        keyboard = get_missions_keyboard(active_missions)
        new_state = "missions"
    elif menu_type == "rewards":
        reward_service = RewardService(session)
        active_rewards = await reward_service.get_active_rewards()
        message_text = BOT_MESSAGES["menu_rewards_text"]
        keyboard = get_reward_keyboard(active_rewards)
        new_state = "rewards"
    elif menu_type == "ranking":
        point_service = PointService(session)
        top_users = await point_service.get_top_users(limit=10) # Asegúrate de que get_top_users exista
        message_text = await get_ranking_message(top_users) # Asegúrate de que get_ranking_message exista
        keyboard = get_ranking_keyboard()
        new_state = "ranking"
    elif menu_type == "back":
        # Lógica de "volver"
        # Simplificamos para siempre volver al menú raíz si estamos en un submenú
        # O si get_parent_menu devuelve algo específico.
        # En este caso, si estamos en un submenú (profile, missions, etc.),
        # queremos volver al menú principal (root).
        if current_state in ["profile", "missions", "rewards", "ranking", "mission_details", "reward_details"]:
            keyboard = get_main_menu_keyboard()
            message_text = BOT_MESSAGES["start_welcome_returning_user"] # Mensaje consistente
            new_state = "root"
        else:
            # Si no estamos en un submenú claro para "volver", ir al menú raíz
            keyboard = get_main_menu_keyboard()
            message_text = BOT_MESSAGES["start_welcome_returning_user"]
            new_state = "root"

    if keyboard:
        await callback.message.edit_text(message_text, reply_markup=keyboard)
        await set_user_menu_state(session, user_id, new_state)
    await callback.answer()


# Handler para comprar una recompensa
@router.callback_query(F.data.startswith("buy_reward_"))
async def handle_buy_reward_callback(callback: CallbackQuery, session: AsyncSession):
    user_id = callback.from_user.id
    reward_id = int(callback.data.split('_')[2]) # Extract reward_id from "buy_reward_X"

    reward_service = RewardService(session)
    reward = await reward_service.get_reward_by_id(reward_id)

    if not reward:
        await callback.answer("Recompensa no encontrada.", show_alert=True)
        return

    # Mensaje de confirmación antes de la compra
    confirmation_message = BOT_MESSAGES["confirm_purchase_message"].format(
        reward_name=reward.name,
        reward_cost=reward.cost
    )
    confirm_keyboard = get_confirm_purchase_keyboard(reward_id)
    
    await callback.message.edit_text(confirmation_message, reply_markup=confirm_keyboard)
    await callback.answer()

# Handler para confirmar la compra de una recompensa
@router.callback_query(F.data.startswith("confirm_purchase_"))
async def handle_confirm_purchase_callback(callback: CallbackQuery, session: AsyncSession):
    user_id = callback.from_user.id
    reward_id = int(callback.data.split('_')[2])

    reward_service = RewardService(session)
    success, message = await reward_service.purchase_reward(user_id, reward_id)

    if success:
        # Refrescar la vista de recompensas después de la compra
        active_rewards = await reward_service.get_active_rewards()
        await callback.message.edit_text(
            f"✅ {message}\n\n{BOT_MESSAGES['menu_rewards_text']}",
            reply_markup=get_reward_keyboard(active_rewards)
        )
    else:
        await callback.answer(f"❌ {message}", show_alert=True)
    await callback.answer() # Siempre responde al callback


# Handler para cancelar la compra de una recompensa
@router.callback_query(F.data.startswith("cancel_purchase_"))
async def handle_cancel_purchase_callback(callback: CallbackQuery, session: AsyncSession):
    user_id = callback.from_user.id
    reward_id = int(callback.data.split('_')[2]) # Si necesitas el reward_id para algo, aunque aquí no sea esencial

    reward_service = RewardService(session)
    active_rewards = await reward_service.get_active_rewards()
    
    await callback.message.edit_text(
        BOT_MESSAGES["purchase_cancelled_message"], # Mensaje de cancelación
        reply_markup=get_reward_keyboard(active_rewards)
    )
    await callback.answer("Compra cancelada.")


# Handler para ver detalles de una misión
@router.callback_query(F.data.startswith("mission_"))
async def handle_mission_details_callback(callback: CallbackQuery, session: AsyncSession):
    user_id = callback.from_user.id
    mission_id = callback.data[len("mission_"):]

    mission_service = MissionService(session)
    mission = await mission_service.get_mission_by_id(mission_id)

    if not mission:
        await callback.answer("Misión no encontrada.", show_alert=True)
        return

    mission_details_message = await get_mission_details_message(mission)
    
    # Un teclado específico para la misión, con un botón para completarla si es posible
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Completar Misión", callback_data=f"complete_mission_{mission_id}")],
        [InlineKeyboardButton(text="⬅️ Volver a Misiones", callback_data="menu:missions")], # Volver al menú de misiones
        [InlineKeyboardButton(text="🏠 Menú Principal", callback_data="menu_principal")]
    ])
    
    await callback.message.edit_text(mission_details_message, reply_markup=keyboard)
    await set_user_menu_state(session, user_id, "mission_details") # Establecer el estado para detalles de misión
    await callback.answer()


# Handler para completar una misión
@router.callback_query(F.data.startswith("complete_mission_"))
async def handle_complete_mission_callback(callback: CallbackQuery, session: AsyncSession):
    user_id = callback.from_user.id
    mission_id = callback.data[len("complete_mission_"):]

    mission_service = MissionService(session)
    point_service = PointService(session)
    level_service = LevelService(session)
    achievement_service = AchievementService(session)

    user = await session.get(User, user_id)
    mission = await mission_service.get_mission_by_id(mission_id)

    if not user or not mission:
        await callback.answer("Error: Usuario o misión no encontrada.", show_alert=True)
        return

    # Verificar si la misión ya está completada para el período actual
    is_completed_for_period, _ = await mission_service.check_mission_completion_status(user, mission)
    if is_completed_for_period:
        await callback.answer("Ya completaste esta misión. ¡Pronto habrá más!", show_alert=True)
        return

    # Intentar completar la misión
    completed, completed_mission_obj = await mission_service.complete_mission(user_id, mission_id)

    if completed:
        updated_user = await point_service.add_points(user_id, completed_mission_obj.points_reward)
        leveled_up = await level_service.check_for_level_up(updated_user)
        
        # Opcional: Otorgar un logro por la primera misión
        if not user.missions_completed: # Si es la primera misión del usuario
             await achievement_service.grant_achievement(user_id, "first_mission")

        alert_message = f"🎉 ¡Misión '{completed_mission_obj.name}' completada! Ganaste `{completed_mission_obj.points_reward}` puntos."
        if leveled_up:
            alert_message += f"\n\n✨ ¡Felicidades! Has subido al nivel `{updated_user.level}`."

        await callback.answer(alert_message, show_alert=True)

        # Volver al menú de misiones y actualizarlo
        active_missions = await mission_service.get_active_missions(user_id=user_id) # Volver a obtener las misiones activas
        await callback.message.edit_text(
            BOT_MESSAGES["menu_missions_text"],
            reply_markup=get_missions_keyboard(active_missions)
        )
        await set_user_menu_state(session, user_id, "missions") # Volver al estado de misiones
    else:
        # Aquí podrías añadir un mensaje específico si la misión requiere una acción externa
        await callback.answer("No puedes completar esta misión ahora mismo o requiere una acción externa.", show_alert=True)


# Handler para reacción (like/dislike)
@router.callback_query(F.data.startswith("reaction_"))
async def handle_reaction_callback(callback: CallbackQuery, session: AsyncSession):
    user_id = callback.from_user.id
    parts = callback.data.split('_')
    reaction_type = parts[1] # 'like' or 'dislike'
    target_message_id = int(parts[2]) # ID del mensaje al que se reaccionó

    # Asume un servicio para manejar reacciones y puntos
    # Puedes crear un ReactionService o integrar esto en PointService/MissionService
    point_service = PointService(session)
    mission_service = MissionService(session)
    level_service = LevelService(session)
    achievement_service = AchievementService(session)

    # Puntos base por reacción
    base_points_for_reaction = 10 if reaction_type == "like" else 5 # Ejemplo

    user = await session.get(User, user_id)
    if not user:
        await callback.answer("Por favor, inicia con /start antes de reaccionar.", show_alert=True)
        return

    # Verificar si el usuario ya reaccionó a este mensaje para evitar spam de puntos
    if user.channel_reactions and user.channel_reactions.get(str(target_message_id)):
        await callback.answer("Ya has reaccionado a este mensaje.", show_alert=True)
        return

    # Añadir los puntos base
    updated_user = await point_service.add_points(user_id, base_points_for_reaction)
    leveled_up = await level_service.check_for_level_up(updated_user) # Verificar si sube de nivel

    # Marcar el mensaje como reaccionado por el usuario
    if user.channel_reactions is None:
        user.channel_reactions = {}
    user.channel_reactions[str(target_message_id)] = True  # Puedes guardar el timestamp si quieres más detalle
    await session.commit() # Guardar el estado de reacción

    # Verificar si hay misiones relacionadas con la reacción
    mission_completed_message = ""
    # Obtener misiones activas que requieran acción
    active_action_missions = await mission_service.get_active_missions(user_id=user_id, mission_type="reaction") # Asume un tipo 'reaction'
    
    for mission in active_action_missions:
        # Aquí la action_data de la misión debería especificar el message_id y/o reaction_type
        # Ejemplo: mission.action_data = {'target_message_id': X, 'reaction_type': 'like'}
        requires_specific_message = mission.action_data and mission.action_data.get('target_message_id') == target_message_id
        requires_specific_reaction = mission.action_data and mission.action_data.get('reaction_type') == reaction_type

        # Si la misión no requiere una acción específica o si la requiere y coincide
        if mission.requires_action and (not mission.action_data or (requires_specific_message and requires_specific_reaction)):
            # Check if the user has already completed this mission for the current period
            is_completed_for_period, _ = await mission_service.check_mission_completion_status(user, mission, target_message_id=target_message_id) # Pasa target_message_id
            
            if not is_completed_for_period:
                completed, mission_obj = await mission_service.complete_mission(user_id, mission.id, target_message_id=target_message_id)
                if completed:
                    mission_completed_message = f"\n\n🎉 ¡Misión completada: **{mission_obj.name}**! Ganaste `{mission_obj.points_reward}` puntos adicionales."
                    updated_user = await point_service.add_points(user_id, mission_obj.points_reward)
                    leveled_up = await level_service.check_for_level_up(updated_user) or leveled_up # Check level up again after mission points

    alert_message = f"¡Reacción registrada! Ganaste `{base_points_for_reaction}` puntos."
    alert_message += mission_completed_message

    if leveled_up:
        alert_message += f"\n\n✨ ¡Felicidades! Has subido al nivel `{updated_user.level}`."

    await callback.answer(alert_message, show_alert=True)
    logger.info(f"User {user_id} reacted with {reaction_type} to message {target_message_id}. Points awarded.")

# --- Handlers para los botones del ReplyKeyboardMarkup ---
# Estos handlers se activarán cuando el usuario envíe el texto exacto del botón.

@router.message(F.text == "👤 Perfil")
async def show_profile_from_reply_keyboard(message: Message, session: AsyncSession):
    user_id = message.from_user.id
    user = await session.get(User, user_id)
    if user:
        point_service = PointService(session)
        level_service = LevelService(session)
        achievement_service = AchievementService(session)
        mission_service = MissionService(session)
        active_missions = await mission_service.get_active_missions(user_id=user_id)
        profile_message = await get_profile_message(user, active_missions)
        await set_user_menu_state(session, user_id, "profile")
        # Mostrar el perfil con su teclado INLINE específico (para Volver y Menú Principal)
        await message.answer(profile_message, reply_markup=get_profile_keyboard())
    else:
        await message.answer(BOT_MESSAGES["profile_not_registered"])

@router.message(F.text == "🗺 Misiones")
async def show_missions_from_reply_keyboard(message: Message, session: AsyncSession):
    user_id = message.from_user.id
    mission_service = MissionService(session)
    active_missions = await mission_service.get_active_missions(user_id=user_id)
    await set_user_menu_state(session, user_id, "missions")
    await message.answer(BOT_MESSAGES["menu_missions_text"], reply_markup=get_missions_keyboard(active_missions))

@router.message(F.text == "🎁 Recompensas")
async def show_rewards_from_reply_keyboard(message: Message, session: AsyncSession):
    user_id = message.from_user.id
    reward_service = RewardService(session)
    active_rewards = await reward_service.get_active_rewards()
    await set_user_menu_state(session, user_id, "rewards")
    await message.answer(BOT_MESSAGES["menu_rewards_text"], reply_markup=get_reward_keyboard(active_rewards))

@router.message(F.text == "🏆 Ranking")
async def show_ranking_from_reply_keyboard(message: Message, session: AsyncSession):
    user_id = message.from_user.id
    point_service = PointService(session)
    top_users = await point_service.get_top_users(limit=10)
    ranking_message = await get_ranking_message(top_users)
    await set_user_menu_state(session, user_id, "ranking")
    await message.answer(ranking_message, reply_markup=get_ranking_keyboard())

# IMPORTANTE: Este handler debe ir AL FINAL de todos los otros F.text handlers,
# porque si no, podría capturar otros mensajes antes de que sean procesados por handlers más específicos.
@router.message(F.text)
async def handle_unrecognized_text(message: Message, session: AsyncSession):
    # Este handler captura cualquier mensaje de texto que no haya sido manejado por otro handler.
    # Es útil para guiar al usuario si escribe algo que el bot no entiende,
    # o si quieres redirigirlo siempre al menú principal si envía texto arbitrario.
    user_id = message.from_user.id
    current_state = await get_user_menu_state(session, user_id)
    
   # Si el usuario escribe algo que no es un comando o un botón del teclado de respuesta
    # y no está en un estado esperando una entrada específica (como en un FSM State),
    # puedes optar por responder con el menú principal o un mensaje de error.
    
    # Para este ejemplo, simplemente volvemos a enviar el menú principal si no entendemos
    # (y el ReplyKeyboardMarkup ya estará visible).
    await message.answer(
        BOT_MESSAGES["unrecognized_command_text"], # "Comando no reconocido. Aquí está el menú principal:"
        reply_markup=get_main_menu_keyboard() # Opcional: mostrar también el inline menu aquí si quieres que se refresque
    )
    # También puedes registrar este evento para depuración:
    logger.warning(f"Unrecognized message from user {user_id}: {message.text}")