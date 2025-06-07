# utils/keyboard_utils.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from utils.messages import BOT_MESSAGES # <--- NUEVA IMPORTACIÓN

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

def get_missions_keyboard(missions: list, offset: int = 0):
    keyboard = []
    for mission in missions[offset:offset+5]:
        keyboard.append([InlineKeyboardButton(text=f"{mission.name} ({mission.points_reward} Pts)", callback_data=f"mission_{mission.id}")])

    nav_buttons = []
    if offset > 0:
        nav_buttons.append(InlineKeyboardButton(text=BOT_MESSAGES["prev_page_button_text"], callback_data=f"missions_nav_{max(0, offset-5)}"))
    if offset + 5 < len(missions):
        nav_buttons.append(InlineKeyboardButton(text=BOT_MESSAGES["next_page_button_text"], callback_data=f"missions_nav_{offset+5}"))
    if nav_buttons:
        keyboard.append(nav_buttons)
    keyboard.append([InlineKeyboardButton(text=BOT_MESSAGES["back_to_main_menu_button_text"], callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_reward_keyboard(rewards: list, offset: int = 0):
    keyboard = []
    for reward in rewards[offset:offset+5]:
        stock_info = f" ({reward.stock} unid.)" if reward.stock != -1 else ""
        keyboard.append([InlineKeyboardButton(text=f"{reward.name} ({reward.cost} Pts){stock_info}", callback_data=f"reward_{reward.id}")])

    nav_buttons = []
    if offset > 0:
        nav_buttons.append(InlineKeyboardButton(text=BOT_MESSAGES["prev_page_button_text"], callback_data=f"rewards_nav_{max(0, offset-5)}"))
    if offset + 5 < len(rewards):
        nav_buttons.append(InlineKeyboardButton(text=BOT_MESSAGES["next_page_button_text"], callback_data=f"rewards_nav_{offset+5}"))
    if nav_buttons:
        keyboard.append(nav_buttons)
    keyboard.append([InlineKeyboardButton(text=BOT_MESSAGES["back_to_main_menu_button_text"], callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_confirm_purchase_keyboard(reward_id: int, reward_cost: int):
    # Usar el mensaje personalizado para el botón de compra
    confirm_text = BOT_MESSAGES["confirm_purchase_button_text"].format(cost=reward_cost)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=confirm_text, callback_data=f"purchase_{reward_id}")],
        [InlineKeyboardButton(text=BOT_MESSAGES["cancel_purchase_button_text"], callback_data=f"reward_{reward_id}")] # Volver a la recompensa específica
    ])
    return keyboard

def get_ranking_keyboard(offset: int = 0, total_users: int = 0):
    keyboard = []
    nav_buttons = []
    # Show 10 users per page for ranking
    if offset > 0:
        nav_buttons.append(InlineKeyboardButton(text=BOT_MESSAGES["prev_page_button_text"], callback_data=f"ranking_nav_{max(0, offset-10)}"))
    if offset + 10 < total_users:
        nav_buttons.append(InlineKeyboardButton(text=BOT_MESSAGES["next_page_button_text"], callback_data=f"ranking_nav_{offset+10}"))
    if nav_buttons:
        keyboard.append(nav_buttons)
    keyboard.append([InlineKeyboardButton(text=BOT_MESSAGES["back_to_main_menu_button_text"], callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_admin_main_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Crear Recompensa", callback_data="admin_create_reward")],
        [InlineKeyboardButton(text="📝 Crear Misión", callback_data="admin_create_mission")],
        [InlineKeyboardButton(text="🔥 Activar Evento", callback_data="admin_activate_event")],
        [InlineKeyboardButton(text="📊 Exportar Datos", callback_data="admin_export_data")],
        [InlineKeyboardButton(text="🔄 Resetear Temporada", callback_data="admin_reset_season")],
        [InlineKeyboardButton(text="🎁 Asignar Puntos", callback_data="admin_assign_points")],
        [InlineKeyboardButton(text="🔙 Menú Principal", callback_data="main_menu")]
    ])
    return keyboard
    
