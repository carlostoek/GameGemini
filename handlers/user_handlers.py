# handlers/user_handlers.py
import datetime
from aiogram import Router, F, Bot # Asegúrate de importar Bot aquí
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton # Import for external actions in channel
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
    get_root_menu, get_parent_menu, get_child_menu # <--- ¡AÑADE ESTAS LÍNEAS!
)
from utils.message_utils import get_profile_message, get_mission_details_message, get_reward_details_message
from config import Config
import asyncio
import logging

logger = logging.getLogger(__name__)

router = Router()

@router.callback_query(F.data == "menu_principal")
async def go_to_main_menu(callback: CallbackQuery, session: AsyncSession):
    user_id = callback.from_user.id
    await set_user_menu_state(session, user_id, "root") # Establecer estado a 'root'
    await callback.message.edit_text("Has vuelto al menú principal:", reply_markup=get_main_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("menu:"))
async def menu_callback_handler(callback: CallbackQuery, session: AsyncSession):
    user_id = callback.from_user.id
    menu_data = callback.data.split(":")[1]
    
    user = await session.get(User, user_id)
    if not user:
        # Esto no debería pasar si el usuario es creado en /start, pero como fallback
        user = User(id=user_id)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        logger.warning(f"User {user_id} not found in menu_callback_handler, created new placeholder.")


    if menu_data == "profile":
        await set_user_menu_state(session, user_id, "profile") # Actualizar estado
        profile_message = await get_profile_message(user, []) # Pasar user y una lista vacía para misiones activas por ahora
        profile_keyboard = get_profile_keyboard()
        await callback.message.edit_text(profile_message, reply_markup=profile_keyboard, parse_mode="Markdown")
        await callback.answer()

    elif menu_data == "missions":
        await set_user_menu_state(session, user_id, "missions") # Actualizar estado
        mission_service = MissionService(session)
        active_missions = await mission_service.get_active_missions(user_id=user_id)
        missions_keyboard = get_missions_keyboard(active_missions)
        
        if not active_missions:
            await callback.message.edit_text("No hay misiones activas en este momento. ¡Vuelve pronto!", reply_markup=missions_keyboard)
        else:
            await callback.message.edit_text("🎯 *Misiones disponibles*\\n\\nElige una misión para ver sus detalles:", reply_markup=missions_keyboard, parse_mode="Markdown")
        await callback.answer()

    elif menu_data == "rewards":
        await set_user_menu_state(session, user_id, "rewards") # Actualizar estado
        reward_service = RewardService(session)
        active_rewards = await reward_service.get_active_rewards()
        rewards_keyboard = get_reward_keyboard(active_rewards)
        
        if not active_rewards:
            await callback.message.edit_text("No hay recompensas disponibles en este momento. ¡Vuelve pronto!", reply_markup=rewards_keyboard)
        else:
            await callback.message.edit_text("🎁 *Recompensas disponibles*\\n\\nAquí puedes ver y canjear tus recompensas:", reply_markup=rewards_keyboard, parse_mode="Markdown")
        await callback.answer()

    elif menu_data == "ranking":
        await set_user_menu_state(session, user_id, "ranking") # Actualizar estado
        point_service = PointService(session)
        top_users = await point_service.get_top_users(limit=10)
        
        ranking_message = "*🏆 Tabla de Posiciones*\\n\\n"
        if top_users:
            for i, u in enumerate(top_users):
                ranking_message += f"{i+1}. {u.first_name or u.username or f'Usuario {u.id}'} - {u.points} Puntos\\n"
        else:
            ranking_message += "Aún no hay usuarios en el ranking."
        
        await callback.message.edit_text(ranking_message, reply_markup=get_ranking_keyboard(), parse_mode="Markdown")
        await callback.answer()

    elif menu_data == "back":
        # La lógica de 'back' debe ser más robusta o siempre volver al principal.
        # Dada la persistencia de `menu_state` y la implementación actual,
        # 'menu:back' debe usar get_parent_menu() para determinar a dónde ir.
        current_state = await get_user_menu_state(session, user_id)
        
        # Si el usuario está en el perfil, misiones, recompensas o ranking,
        # "back" debería llevarlo al menú principal.
        # keyboard_utils.get_parent_menu ya tiene la lógica de fallback a root.
        new_keyboard = get_parent_menu(current_state) # current_state será 'profile', 'missions', etc.
        
        # Restablecer el estado del menú a "root" después de volver
        await set_user_menu_state(session, user_id, "root")
        
        await callback.message.edit_text("Volviendo al menú principal:", reply_markup=new_keyboard)
        await callback.answer()

    else:
        await callback.answer("Opción de menú no reconocida.", show_alert=True)


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession):
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name

    point_service = PointService(session)
    user = await session.get(User, user_id)

    if not user:
        # Nuevo usuario
        user = User(id=user_id, username=username, first_name=first_name, last_name=last_name)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        await message.answer(
            "🌙 Bienvenid@ a *El Diván de Diana*…\n\n"
            "Aquí cada gesto, cada decisión y cada paso que das, suma. Con cada interacción, te adentras más en *El Juego del Diván*.\n\n"
            "¿Estás list@ para descubrir lo que te espera? Elige por dónde empezar, yo me encargo de hacer que lo disfrutes.",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="Markdown"
        )
        logger.info(f"New user registered: {user_id} ({username})")
    else:
        # Usuario existente
        await message.answer(
            "✨ Qué bueno tenerte de regreso.\n\n"
            "Tu lugar sigue aquí. Tus puntos también... y hay nuevas sorpresas esperándote.\n\n"
            "¿List@ para continuar *El Juego del Diván*?",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="Markdown"
        )
        logger.info(f"Returning user: {user_id} ({username})")
    
    await set_user_menu_state(session, user_id, "root") # Asegurar que el estado del menú se inicializa a 'root' al inicio


@router.message(F.text)
async def handle_text_messages(message: Message, session: AsyncSession):
    # Esto es un handler genérico para mensajes de texto que no son comandos o callbacks
    # Podrías implementar aquí lógica para respuestas a preguntas, etc.
    # Por ahora, simplemente reenvía el menú principal si no se reconoce.
    user_id = message.from_user.id
    text = message.text.lower()
    
    # Podrías tener una lógica para estados FSM aquí si el usuario está en un flujo conversacional
    # Por ejemplo, si el usuario está en un estado de "pregunta de trivia", manejar la respuesta.

    # Default fallback: show main menu if no specific handler
    await message.answer("Lo siento, no entendí tu mensaje. Aquí tienes el menú principal:", reply_markup=get_main_menu_keyboard())
    await set_user_menu_state(session, user_id, "root") # Asegurar que el estado se restablece a 'root'
    logger.info(f"User {user_id} sent unrecognized text: '{message.text}'")


@router.callback_query(F.data.startswith("mission_"))
async def mission_details_callback(callback: CallbackQuery, session: AsyncSession):
    user_id = callback.from_user.id
    mission_id = callback.data.split("_")[1]
    
    mission_service = MissionService(session)
    mission = await mission_service.get_mission_by_id(mission_id)
    
    if mission:
        details_message = await get_mission_details_message(mission)
        
        # Keyboard for mission details
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Marcar como Completado", callback_data=f"complete_mission_{mission.id}")],
            [InlineKeyboardButton(text="⬅️ Volver a Misiones", callback_data="menu:missions")], # <-- Vuelve al menú de misiones
            [InlineKeyboardButton(text="🏠 Menú Principal", callback_data="menu_principal")]
        ])
        
        await callback.message.edit_text(details_message, reply_markup=keyboard, parse_mode="Markdown")
        await callback.answer()
    else:
        await callback.answer("Misión no encontrada.", show_alert=True)
        await callback.message.edit_text("Volviendo al menú de misiones.", reply_markup=get_missions_keyboard([])) # Fallback

@router.callback_query(F.data.startswith("complete_mission_"))
async def complete_mission_callback(callback: CallbackQuery, session: AsyncSession):
    user_id = callback.from_user.id
    mission_id = callback.data.split("_")[2]

    mission_service = MissionService(session)
    point_service = PointService(session)
    level_service = LevelService(session)
    achievement_service = AchievementService(session)

    user = await session.get(User, user_id)
    if not user:
        await callback.answer("Usuario no encontrado.", show_alert=True)
        return

    mission = await mission_service.get_mission_by_id(mission_id)
    if not mission:
        await callback.answer("Misión no encontrada.", show_alert=True)
        return

    # Check if the mission requires an action (e.g., reaction)
    if mission.requires_action and mission.type != 'reaction': # Exclude reaction missions from this check as they are completed differently
        await callback.answer("Esta misión requiere una acción específica fuera de este menú para ser completada.", show_alert=True)
        return
    
    # Check if the user has already completed this mission for the current period
    is_completed_for_period, _ = await mission_service.check_mission_completion_status(user, mission)
    if is_completed_for_period:
        await callback.answer("Ya has completado esta misión para el período actual.", show_alert=True)
        return

    # For missions that don't require external action, mark as completed
    completed, mission_obj = await mission_service.complete_mission(user_id, mission.id)
    
    if completed:
        updated_user = await point_service.add_points(user_id, mission_obj.points_reward)
        leveled_up = await level_service.check_for_level_up(updated_user)

        # Check for achievements after mission completion
        if await achievement_service.grant_achievement(user_id, "first_mission"):
            await callback.message.answer("¡Felicidades! Has desbloqueado el logro 'Primera Misión Completada' 🏅", parse_mode="Markdown")

        alert_message = f"🎉 ¡Misión completada: **{mission_obj.name}**! Ganaste `{mission_obj.points_reward}` puntos."
        if leveled_up:
            alert_message += f"\\n\\n✨ ¡Felicidades! Has subido al nivel `{updated_user.level}`."
            
        await callback.answer(alert_message, show_alert=True)
        # Update the message with new missions list
        await callback.message.edit_text(
            "🎯 *Misiones disponibles*\\n\\nElige una misión para ver sus detalles:",
            reply_markup=get_missions_keyboard(await mission_service.get_active_missions(user_id=user_id)),
            parse_mode="Markdown"
        )
    else:
        await callback.answer("No se pudo completar la misión.", show_alert=True)

@router.callback_query(F.data.startswith("reward_"))
async def reward_details_callback(callback: CallbackQuery, session: AsyncSession):
    user_id = callback.from_user.id
    reward_id = int(callback.data.split("_")[1])
    
    reward_service = RewardService(session)
    reward = await reward_service.get_reward_by_id(reward_id)
    user = await session.get(User, user_id)

    if reward and user:
        details_message = await get_reward_details_message(reward, user.points)
        
        # Keyboard for reward details
        keyboard = get_confirm_purchase_keyboard(reward.id, reward.cost, user.points >= reward.cost and (reward.stock == -1 or reward.stock > 0))
        
        await callback.message.edit_text(details_message, reply_markup=keyboard, parse_mode="Markdown")
        await callback.answer()
    else:
        await callback.answer("Recompensa no encontrada o usuario no válido.", show_alert=True)
        await callback.message.edit_text("Volviendo al menú de recompensas.", reply_markup=get_reward_keyboard([])) # Fallback


@router.callback_query(F.data.startswith("purchase_reward_"))
async def confirm_purchase_reward_callback(callback: CallbackQuery, session: AsyncSession):
    user_id = callback.from_user.id
    reward_id = int(callback.data.split("_")[2])

    reward_service = RewardService(session)
    achievement_service = AchievementService(session)

    success, message = await reward_service.purchase_reward(user_id, reward_id)
    leveled_up = False # Initialize leveled_up flag

    if success:
        # Check for first purchase achievement
        if await achievement_service.grant_achievement(user_id, "first_purchase"):
            await callback.message.answer("¡Felicidades! Has desbloqueado el logro 'Primer Comprador' 💰", parse_mode="Markdown")

        # Refrescar datos del usuario después de la compra para verificar el nivel
        user = await session.get(User, user_id)
        if user:
            level_service = LevelService(session) # Instanciar LevelService
            leveled_up = await level_service.check_for_level_up(user) # Verificar si subió de nivel

        alert_message = message
        if leveled_up:
            alert_message += f"\\n\\n✨ ¡Felicidades! Has subido al nivel `{user.level}`."

        await callback.answer(alert_message, show_alert=True)
        # Update the message with new rewards list
        await callback.message.edit_text(
            "🎁 *Recompensas disponibles*\\n\\nAquí puedes ver y canjear tus recompensas:",
            reply_markup=get_reward_keyboard(await reward_service.get_active_rewards()),
            parse_mode="Markdown"
        )

    else:
        await callback.answer(message, show_alert=True)


@router.callback_query(F.data.startswith("cancel_purchase_"))
async def cancel_purchase_reward_callback(callback: CallbackQuery, session: AsyncSession):
    await callback.answer("Compra cancelada.", show_alert=True)
    reward_service = RewardService(session)
    # Return to rewards menu
    await callback.message.edit_text(
        "🎁 *Recompensas disponibles*\\n\\nAquí puedes ver y canjear tus recompensas:",
        reply_markup=get_reward_keyboard(await reward_service.get_active_rewards()),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("react_"))
async def handle_reaction_callback(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    user_id = callback.from_user.id
    parts = callback.data.split('_')
    reaction_type = parts[1] # e.g., 'like', 'love', 'insight'
    message_id = int(parts[2]) # The ID of the channel post

    point_service = PointService(session)
    mission_service = MissionService(session)
    level_service = LevelService(session)

    # Fetch the user to check if they've already reacted to this specific message
    user = await session.get(User, user_id)
    if not user:
        await callback.answer("Usuario no encontrado. Por favor, inicia con /start.", show_alert=True)
        return

    # Check if the user has already reacted to this specific message
    if str(message_id) in user.channel_reactions and user.channel_reactions[str(message_id)]:
        await callback.answer("Ya reaccionaste a esta publicación.", show_alert=True)
        return

    # Define base points for reaction (can be customized)
    base_points_for_reaction = 10 # Example points for any reaction

    # Add points to user for the reaction
    updated_user = await point_service.add_points(user_id, base_points_for_reaction)
    leveled_up = await level_service.check_for_level_up(updated_user) # Check for level up immediately

    # Mark the message as reacted by the user
    user.channel_reactions[str(message_id)] = True
    session.add(user) # Mark user as modified for SQLAlchemy to detect JSON update
    await session.commit()
    await session.refresh(user)

    mission_completed_message = ""
    # Check for reaction-based missions
    # Assuming action_data for reaction missions would be {'target_message_id': [message_id], 'reaction_type': 'like'}
    # Or simply mission.type == 'reaction' and check if user reacted to ANY channel post.
    
    # Get active reaction missions
    reaction_missions = await mission_service.get_active_missions(user_id=user_id, mission_type='reaction')

    for mission in reaction_missions:
        # Check if this mission is tied to a specific message_id or reaction_type if needed.
        # For a generic 'react to any post' mission, no specific action_data needed.
        # If mission has specific action_data, e.g., {'target_message_id': [123, 456]}, check against it.
        # For example: if mission.action_data and message_id not in mission.action_data.get('target_message_id', []): continue
        # Or if mission.action_data and reaction_type != mission.action_data.get('reaction_type'): continue

        # Check if the user has already completed this mission for the current period
        is_completed_for_period, _ = await mission_service.check_mission_completion_status(user, mission, target_message_id=message_id) # Pass message_id for specific mission tracking
        
        if not is_completed_for_period:
            completed, mission_obj = await mission_service.complete_mission(user_id, mission.id, target_message_id=message_id) # Pass message_id as target for mission completion
            if completed:
                mission_completed_message = f"\\n\\n🎉 ¡Misión completada: **{mission_obj.name}**! Ganaste `{mission_obj.points_reward}` puntos adicionales."
                # Asumimos que add_points ya maneja el multiplicador de eventos si hay uno activo
                updated_user = await point_service.add_points(user_id, mission_obj.points_reward)
                leveled_up = await level_service.check_for_level_up(updated_user) or leveled_up # Check level up again after mission points


    # Prepare the alert message
    alert_message = f"¡Reacción registrada! Ganaste `{base_points_for_reaction}` puntos."
    alert_message += mission_completed_message # Add mission completion message if any

    if leveled_up:
        alert_message += f"\\n\\n✨ ¡Felicidades! Has subido al nivel `{updated_user.level}`."

    await callback.answer(alert_message, show_alert=True)
    logger.info(f"User {user_id} reacted with {reaction_type} to message {message_id} in channel.")

