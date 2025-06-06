from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

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
        [InlineKeyboardButton(text="Ver Logros", callback_data="profile_achievements")],
        [InlineKeyboardButton(text="Ver Misiones Activas", callback_data="profile_missions_active")],
        [InlineKeyboardButton(text="🔙 Volver al Menú Principal", callback_data="main_menu")]
    ])
    return keyboard

def get_missions_keyboard(missions: list, offset: int = 0):
    keyboard = []
    # Display up to 5 missions per page
    for mission in missions[offset:offset+5]:
        keyboard.append([InlineKeyboardButton(text=f"{mission.name} ({mission.points_reward} Pts)", callback_data=f"mission_{mission.id}")])

    nav_buttons = []
    if offset > 0:
        nav_buttons.append(InlineKeyboardButton(text="◀️ Anterior", callback_data=f"missions_nav_{max(0, offset-5)}"))
    if offset + 5 < len(missions):
        nav_buttons.append(InlineKeyboardButton(text="Siguiente ▶️", callback_data=f"missions_nav_{offset+5}"))
    if nav_buttons:
        keyboard.append(nav_buttons)

    keyboard.append([InlineKeyboardButton(text="🔙 Volver al Menú Principal", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_reward_keyboard(rewards: list, offset: int = 0):
    keyboard = []
    # Display up to 5 rewards per page
    for reward in rewards[offset:offset+5]:
        stock_info = f" ({reward.stock} disp.)" if reward.stock != -1 else ""
        keyboard.append([InlineKeyboardButton(text=f"{reward.name} ({reward.cost} Pts){stock_info}", callback_data=f"reward_{reward.id}")])

    nav_buttons = []
    if offset > 0:
        nav_buttons.append(InlineKeyboardButton(text="◀️ Anterior", callback_data=f"rewards_nav_{max(0, offset-5)}"))
    if offset + 5 < len(rewards):
        nav_buttons.append(InlineKeyboardButton(text="Siguiente ▶️", callback_data=f"rewards_nav_{offset+5}"))
    if nav_buttons:
        keyboard.append(nav_buttons)

    keyboard.append([InlineKeyboardButton(text="🔙 Volver al Menú Principal", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_confirm_purchase_keyboard(reward_id: int):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Confirmar Compra", callback_data=f"confirm_purchase_{reward_id}")],
        [InlineKeyboardButton(text="❌ Cancelar", callback_data="store_menu")] # A general store_menu callback might be useful
    ])
    return keyboard

def get_ranking_keyboard(offset: int = 0, total_users: int = 0):
    keyboard = []
    nav_buttons = []
    # Show 10 users per page for ranking
    if offset > 0:
        nav_buttons.append(InlineKeyboardButton(text="◀️ Anterior", callback_data=f"ranking_nav_{max(0, offset-10)}"))
    if offset + 10 < total_users:
        nav_buttons.append(InlineKeyboardButton(text="Siguiente ▶️", callback_data=f"ranking_nav_{offset+10}"))
    if nav_buttons:
        keyboard.append(nav_buttons)
    keyboard.append([InlineKeyboardButton(text="🔙 Volver al Menú Principal", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_admin_main_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Crear Recompensa", callback_data="admin_create_reward")],
        [InlineKeyboardButton(text="📝 Crear Misión", callback_data="admin_create_mission")],
        [InlineKeyboardButton(text="🔥 Activar Evento", callback_data="admin_activate_event")],
        [InlineKeyboardButton(text="📊 Exportar Datos", callback_data="admin_export_data")],
        [InlineKeyboardButton(text="🔄 Resetear Temporada", callback_data="admin_reset_season")],
        [InlineKeyboardButton(text="🔙 Volver al Menú Principal", callback_data="main_menu")]
    ])
    return keyboard
