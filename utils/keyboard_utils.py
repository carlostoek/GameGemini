# utils/keyboard_utils.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from database.models import User


def get_main_menu_keyboard():
    """Returns the main inline menu keyboard."""
    keyboard = [
        [InlineKeyboardButton(text="👤 Perfil", callback_data="menu:profile")],
        [InlineKeyboardButton(text="🗺 Misiones", callback_data="menu:missions")],
        [InlineKeyboardButton(text="🎁 Recompensas", callback_data="menu:rewards")],
        [InlineKeyboardButton(text="🏆 Ranking", callback_data="menu:ranking")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_profile_keyboard():
    """Returns the keyboard for the profile section."""
    keyboard = [
        [InlineKeyboardButton(text="🏠 Menú Principal", callback_data="menu_principal")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_missions_keyboard(missions: list, offset: int = 0):
    """Returns the keyboard for missions, with pagination."""
    keyboard = []
    # Display up to 5 missions per page
    for mission in missions[offset:offset+5]:
        keyboard.append([InlineKeyboardButton(text=f"{mission.name} ({mission.points_reward} Pts)", callback_data=f"mission_{mission.id}")])
    
    # Add navigation buttons if there are more missions
    nav_buttons = []
    if offset > 0:
        nav_buttons.append(InlineKeyboardButton(text="← Anterior", callback_data=f"missions_page_{offset - 5}"))
    if offset + 5 < len(missions):
        nav_buttons.append(InlineKeyboardButton(text="Siguiente →", callback_data=f"missions_page_{offset + 5}"))
    if nav_buttons:
        keyboard.append(nav_buttons)

    keyboard.append([InlineKeyboardButton(text="🏠 Menú Principal", callback_data="menu_principal")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_reward_keyboard(rewards: list):
    """Returns the keyboard for rewards."""
    keyboard = []
    for reward in rewards:
        keyboard.append([InlineKeyboardButton(text=f"{reward.name} ({reward.cost} Pts)", callback_data=f"buy_reward_{reward.id}")])
    keyboard.append([InlineKeyboardButton(text="🏠 Menú Principal", callback_data="menu_principal")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_confirm_purchase_keyboard(reward_id: int):
    """Returns the confirmation keyboard for reward purchase."""
    keyboard = [
        [InlineKeyboardButton(text="✅ Confirmar", callback_data=f"confirm_purchase_{reward_id}")],
        [InlineKeyboardButton(text="❌ Cancelar", callback_data=f"cancel_purchase_{reward_id}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_ranking_keyboard():
    """Returns the keyboard for the ranking section."""
    keyboard = [
        [InlineKeyboardButton(text="🏠 Menú Principal", callback_data="menu_principal")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_reaction_keyboard(message_id: int):
    """Returns an inline keyboard with like/dislike buttons for channel posts."""
    keyboard = [
        [
            InlineKeyboardButton(text="👍 Me gusta", callback_data=f"reaction_like_{message_id}"),
            InlineKeyboardButton(text="👎 No me gusta", callback_data=f"reaction_dislike_{message_id}")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_admin_main_keyboard():
    """Returns the top level keyboard for admin actions."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🧑‍💼 Gestionar Usuarios", callback_data="admin_manage_users")],
        [InlineKeyboardButton(text="🎮 Gestionar Contenido/Juego", callback_data="admin_manage_content")],
        [InlineKeyboardButton(text="🎉 Gestionar Eventos y Sorteos", callback_data="admin_manage_events_sorteos")],
        [InlineKeyboardButton(text="⚙️ Configuración del Bot", callback_data="admin_bot_config")],
        [InlineKeyboardButton(text="🔙 Menú Principal", callback_data="menu_principal")]
    ])
    return keyboard

def get_admin_manage_users_keyboard():
    """Returns the keyboard for user management options in the admin panel."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Sumar Puntos a Usuario", callback_data="admin_add_points")],
        [InlineKeyboardButton(text="➖ Restar Puntos a Usuario", callback_data="admin_deduct_points")],
        [InlineKeyboardButton(text="🔍 Ver Perfil de Usuario", callback_data="admin_view_user")],
        [InlineKeyboardButton(text="🔎 Buscar Usuario", callback_data="admin_search_user")],
        [InlineKeyboardButton(text="📢 Notificar a Usuarios", callback_data="admin_notify_users")],
        [InlineKeyboardButton(text="🔙 Volver al Menú Principal de Administrador", callback_data="admin_main_menu")]
    ])
    return keyboard

def get_admin_manage_content_keyboard():
    """Returns the keyboard for content management options."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📌 Misiones", callback_data="admin_content_missions")],
        [InlineKeyboardButton(text="🏅 Insignias", callback_data="admin_content_badges")],
        [InlineKeyboardButton(text="📈 Niveles", callback_data="admin_content_levels")],
        [InlineKeyboardButton(text="🎁 Recompensas (Catálogo VIP)", callback_data="admin_content_rewards")],
        [InlineKeyboardButton(text="📦 Subastas", callback_data="admin_content_auctions")],
        [InlineKeyboardButton(text="🎁 Regalos Diarios", callback_data="admin_content_daily_gifts")],
        [InlineKeyboardButton(text="🔙 Volver al Menú Principal de Administrador", callback_data="admin_main_menu")]
    ])
    return keyboard

def get_admin_content_missions_keyboard():
    """Keyboard for mission management options."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Crear Misión", callback_data="admin_create_mission")],
        [InlineKeyboardButton(text="🔄 Activar / Desactivar Misión", callback_data="admin_toggle_mission")],
        [InlineKeyboardButton(text="📃 Ver Misiones Activas", callback_data="admin_view_active_missions")],
        [InlineKeyboardButton(text="🔙 Volver", callback_data="admin_manage_content")]
    ])
    return keyboard

def get_admin_content_badges_keyboard():
    """Keyboard for badge management options."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏆 Otorgar Insignia Manualmente", callback_data="admin_give_badge_manual")],
        [InlineKeyboardButton(text="⚙️ Gestionar Insignias", callback_data="admin_manage_badges")],
        [InlineKeyboardButton(text="🔙 Volver", callback_data="admin_manage_content")]
    ])
    return keyboard

def get_admin_content_levels_keyboard():
    """Keyboard for level management options."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🧩 Ajustar Niveles", callback_data="admin_adjust_levels")],
        [InlineKeyboardButton(text="🔙 Volver", callback_data="admin_manage_content")]
    ])
    return keyboard

def get_admin_content_rewards_keyboard():
    """Keyboard for reward catalogue management options."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Añadir Recompensa", callback_data="admin_create_reward")],
        [InlineKeyboardButton(text="✏️ Editar / Eliminar Recompensa", callback_data="admin_edit_reward")],
        [InlineKeyboardButton(text="📦 Ver Recompensas Canjeadas", callback_data="admin_view_claimed_rewards")],
        [InlineKeyboardButton(text="🔙 Volver", callback_data="admin_manage_content")]
    ])
    return keyboard

def get_admin_content_auctions_keyboard():
    """Keyboard for auction management options."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Crear Subasta", callback_data="admin_create_auction")],
        [InlineKeyboardButton(text="📋 Ver Subastas Activas / Finalizadas", callback_data="admin_view_auctions")],
        [InlineKeyboardButton(text="⛔ Finalizar Subasta Manualmente", callback_data="admin_finish_auction")],
        [InlineKeyboardButton(text="🔙 Volver", callback_data="admin_manage_content")]
    ])
    return keyboard

def get_admin_content_daily_gifts_keyboard():
    """Keyboard for daily gift configuration options."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎯 Configurar Regalo del Día", callback_data="admin_configure_daily_gift")],
        [InlineKeyboardButton(text="🔙 Volver", callback_data="admin_manage_content")]
    ])
    return keyboard

# --- Funciones para la navegación de menú ---
# Estas funciones están más orientadas a la lógica de estado que a la creación de teclados per se,
# pero se mantienen aquí para compatibilidad si las usas para generar teclados dinámicos.

def get_root_menu():
    """Returns the inline keyboard for the root menu."""
    keyboard = [
        [InlineKeyboardButton(text="👤 Perfil", callback_data="menu:profile")],
        [InlineKeyboardButton(text="🗺 Misiones", callback_data="menu:missions")],
        [InlineKeyboardButton(text="🎁 Recompensas", callback_data="menu:rewards")],
        [InlineKeyboardButton(text="🏆 Ranking", callback_data="menu:ranking")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_parent_menu(parent_name: str):
    """Returns the keyboard for a parent menu based on its name."""
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
    """Returns the keyboard for a child menu based on its name."""
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

def get_main_reply_keyboard():
    """
    Returns the main ReplyKeyboardMarkup with persistent buttons.
    This replaces the need for menu_principal callback for direct access from text.
    """
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="👤 Perfil"),
                KeyboardButton(text="🗺 Misiones")
            ],
            [
                KeyboardButton(text="🎁 Recompensas"),
                KeyboardButton(text="🏆 Ranking")
            ]
        ],
        resize_keyboard=True, # Make the keyboard smaller
        one_time_keyboard=False # Keep the keyboard visible
    )
    return keyboard


def get_back_keyboard(callback_data: str) -> InlineKeyboardMarkup:
    """Return a simple keyboard with a single back button."""
    keyboard = [
        [InlineKeyboardButton(text="🔙 Volver", callback_data=callback_data)]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_admin_users_list_keyboard(
    users: list[User], offset: int, total_count: int, limit: int = 5
) -> InlineKeyboardMarkup:
    """Return a keyboard for the paginated list of users with action buttons."""
    keyboard: list[list[InlineKeyboardButton]] = []

    for user in users:
        keyboard.append(
            [
                InlineKeyboardButton(
                    text="➕", callback_data=f"admin_user_add_{user.id}"
                ),
                InlineKeyboardButton(
                    text="➖", callback_data=f"admin_user_deduct_{user.id}"
                ),
                InlineKeyboardButton(
                    text="👁", callback_data=f"admin_user_view_{user.id}"
                ),
            ]
        )

    nav_buttons: list[InlineKeyboardButton] = []
    if offset > 0:
        nav_buttons.append(
            InlineKeyboardButton(
                text="⬅️", callback_data=f"admin_users_page_{offset - limit}"
            )
        )
    if offset + limit < total_count:
        nav_buttons.append(
            InlineKeyboardButton(
                text="➡️", callback_data=f"admin_users_page_{offset + limit}"
            )
        )
    if nav_buttons:
        keyboard.append(nav_buttons)

    keyboard.append([InlineKeyboardButton(text="🔙 Volver", callback_data="admin_main_menu")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)
