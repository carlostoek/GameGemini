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
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=BOT_MESSAGES["profile_achievements_button_text"], callback_data="profile_achievements")],
        [InlineKeyboardButton(text=BOT_MESSAGES["profile_active_missions_button_text"], callback_data="profile_missions_active")],
        [InlineKeyboardButton(text=BOT_MESSAGES["back_to_main_menu_button_text"], callback_data="main_menu")]
    ])
    return keyboard

# 🆕 Generadores de menús inline dinámicos

def get_root_menu() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("🎯 Quiz", callback_data="menu:quiz"),
        InlineKeyboardButton("🎁 Recompensas", callback_data="menu:rewards"),
    )
    return keyboard

def get_parent_menu(menu_name: str) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("🔙 Volver al menú raíz", callback_data="menu:back")
    )
    return keyboard

def get_child_menu(menu_name: str) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=2)

    if menu_name == "quiz":
        keyboard.add(
            InlineKeyboardButton("📅 Participar Hoy", callback_data="quiz:today"),
            InlineKeyboardButton("🔙 Volver", callback_data="menu:back")
        )
    elif menu_name == "rewards":
        keyboard.add(
            InlineKeyboardButton("🏆 Canjear Puntos", callback_data="rewards:redeem"),
            InlineKeyboardButton("🔙 Volver", callback_data="menu:back")
        )
    else:
        keyboard.add(InlineKeyboardButton("🔙 Volver", callback_data="menu:back"))

    return keyboard
