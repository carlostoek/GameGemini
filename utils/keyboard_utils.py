# utils/keyboard_utils.py (Archivo completo con la nueva función incluida)

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from utils.messages import BOT_MESSAGES  # Asegúrate de que esta importación exista

def get_main_menu_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👤 Mi Perfil"), KeyboardButton(text="🎯 Misiones")],
            [KeyboardButton(text="🛍️ Tienda de Recompensas"), KeyboardButton(text="🏆 Ranking")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard

def get_profile_keyboard():
    ...
    # Implementación original de get_profile_keyboard
    ...

def get_missions_keyboard(missions: list, offset: int = 0):
    ...
    # Implementación original de get_missions_keyboard
    ...

def get_reward_keyboard(rewards: list, offset: int = 0):
    """
    Genera un teclado inline con las recompensas activas.
    :param rewards: Lista de objetos Reward con atributos 'id', 'name' y 'cost'.
    :param offset: Desplazamiento para paginación (opcional).
    :return: InlineKeyboardMarkup
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"{reward.name} ({reward.cost} pts)",
                    callback_data=f"reward_{reward.id}"
                )
            ] for reward in rewards
        ]
    )
    return keyboard

def get_admin_main_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Crear Recompensa", callback_data="admin_create_reward")],
        [InlineKeyboardButton(text="📝 Crear Misión", callback_data="admin_create_mission")],
        [InlineKeyboardButton(text="🔥 Activar Evento", callback_data="admin_activate_event")],
        [InlineKeyboardButton(text="📊 Exportar Datos", callback_data="admin_export_data")],
        [InlineKeyboardButton(text="🔄 Resetear Temporada", callback_data="admin_reset_season")],
        [InlineKeyboardButton(text="🎁 Asignar Puntos", callback_data="admin_assign_points")],
        [InlineKeyboardButton(text="📢 Enviar mensaje con reacciones", callback_data="admin_send_channel_post_reactions")],  # NUEVO BOTÓN
        [InlineKeyboardButton(text="🔙 Menú Principal", callback_data="main_menu")]
    ])
    return keyboard

def get_reaction_keyboard(message_id: int):
    # Definimos los botones de reacción que queremos.
    # El callback_data debe ser único e incluir el message_id para saber a qué mensaje se reaccionó.
    # El formato es "reaction_{message_id}_{reaction_type_id}"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💖 Resuena con mi Alma", callback_data=f"reaction_{message_id}_soul"),
            InlineKeyboardButton(text="🤔 Me hace Reflexionar", callback_data=f"reaction_{message_id}_think")
        ],
        [
            InlineKeyboardButton(text="💡 Iluminación Instantánea", callback_data=f"reaction_{message_id}_light"),
            InlineKeyboardButton(text="✨ Pura Inspiración", callback_data=f"reaction_{message_id}_inspire")
        ]
    ])
    return keyboard
