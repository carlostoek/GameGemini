# utils/keyboard_utils.py
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
    # Implementación original de get_profile_keyboard
    ...

def get_missions_keyboard(missions: list, offset: int = 0):
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
    # Implementación original de get_admin_main_keyboard
    ...

def get_reaction_keyboard(message_id: int):
    # Implementación original de get_reaction_keyboard
    ...

def get_confirm_purchase_keyboard(reward_id: int):
    """
    Genera un teclado inline para confirmar o cancelar la compra de una recompensa.
    :param reward_id: ID de la recompensa a comprar.
    :return: InlineKeyboardMarkup
    """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=BOT_MESSAGES['confirm_button_text'],
                callback_data=f'confirm_purchase_{reward_id}'
            ),
            InlineKeyboardButton(
                text=BOT_MESSAGES['cancel_button_text'],
                callback_data='cancel_purchase'
            )
        ]
    ])
    return keyboard

def get_ranking_keyboard():
    """
    Genera un teclado de respuesta con opción de volver al menú principal tras mostrar el ranking.
    :return: ReplyKeyboardMarkup
    """
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔙 Menú Principal")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return keyboard
