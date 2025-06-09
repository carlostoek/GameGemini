from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton(text="👤 Perfil", callback_data="menu:profile")],
        [InlineKeyboardButton(text="🗺 Misiones", callback_data="menu:missions")],
        [InlineKeyboardButton(text="🎁 Recompensas", callback_data="menu:rewards")],
        [InlineKeyboardButton(text="🏆 Ranking", callback_data="menu:ranking")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_profile_keyboard():
    keyboard = [
        [InlineKeyboardButton(text="⬅️ Volver al menú", callback_data="menu:back")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_missions_keyboard(missions: list, offset: int = 0):
    keyboard = []
    for mission in missions[offset:offset+5]:
        keyboard.append([InlineKeyboardButton(text=f"{mission.name} ({mission.points_reward} Pts)", callback_data=f"mission_{mission.id}")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_reward_keyboard(rewards: list):
    keyboard = []
    for reward in rewards:
        keyboard.append([InlineKeyboardButton(text=f"{reward.name} ({reward.cost} Pts)", callback_data=f"reward_{reward.id}")])
    keyboard.append([InlineKeyboardButton(text="⬅️ Volver al menú", callback_data="menu:back")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_confirm_purchase_keyboard(reward_id: int):
    keyboard = [
        [
            InlineKeyboardButton(text="✅ Confirmar", callback_data=f"confirm_purchase:{reward_id}"),
            InlineKeyboardButton(text="❌ Cancelar", callback_data="cancel_purchase")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_ranking_keyboard():
    keyboard = [
        [InlineKeyboardButton(text="⬅️ Volver al menú", callback_data="menu:back")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_reaction_keyboard(message_id: int):
    keyboard = [
        [InlineKeyboardButton(text="❤️ Reaccionar", callback_data=f"react:{message_id}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_admin_main_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Crear Recompensa", callback_data="admin_create_reward")],
        [InlineKeyboardButton(text="📝 Crear Misión", callback_data="admin_create_mission")],
        [InlineKeyboardButton(text="🔥 Activar Evento", callback_data="admin_activate_event")],
        [InlineKeyboardButton(text="📊 Exportar Datos", callback_data="admin_export_data")],
        [InlineKeyboardButton(text="🔄 Resetear Temporada", callback_data="admin_reset_season")],
        [InlineKeyboardButton(text="🎁 Asignar Puntos", callback_data="admin_assign_points")],
        [InlineKeyboardButton(text="📢 Enviar mensaje con reacciones al Canal", callback_data="admin_send_channel_post_reactions")],
        [InlineKeyboardButton(text="🔙 Menú Principal", callback_data="main_menu")]
    ])
    return keyboard


def get_root_menu():
    keyboard = [
        [InlineKeyboardButton(text="👤 Perfil", callback_data="menu:profile")],
        [InlineKeyboardButton(text="🗺 Misiones", callback_data="menu:missions")],
        [InlineKeyboardButton(text="🎁 Recompensas", callback_data="menu:rewards")],
        [InlineKeyboardButton(text="🏆 Ranking", callback_data="menu:ranking")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_parent_menu(parent_name: str):
    if parent_name == "profile":
        return get_profile_keyboard()
    elif parent_name == "missions":
        return get_missions_keyboard([])  # Puedes adaptar esto si quieres mostrar misiones
    elif parent_name == "rewards":
        return get_reward_keyboard([])
    elif parent_name == "ranking":
        return get_ranking_keyboard()
    else:
        return get_root_menu()


def get_child_menu(menu_name: str):
    if menu_name == "profile":
        return get_profile_keyboard()
    elif menu_name == "missions":
        return get_missions_keyboard([])
    elif menu_name == "rewards":
        return get_reward_keyboard([])
    elif menu_name == "ranking":
        return get_ranking_keyboard()
    else:
        return get_root_menu()
        
