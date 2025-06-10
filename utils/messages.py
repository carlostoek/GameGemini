# utils/messages.py
BOT_MESSAGES = {
    "start_welcome_new_user": (
        "🌙 Bienvenid@ a *El Diván de Diana*…\n\n"
        "Aquí cada gesto, cada decisión y cada paso que das, suma. Con cada interacción, te adentras más en *El Juego del Diván*.\n\n"
        "¿Estás list@ para descubrir lo que te espera? Elige por dónde empezar, yo me encargo de hacer que lo disfrutes."
    ),
    "start_welcome_returning_user": (
        "✨ Qué bueno tenerte de regreso.\n\n"
        "Tu lugar sigue aquí. Tus puntos también... y hay nuevas sorpresas esperándote.\n\n"
        "¿List@ para continuar *El Juego del Diván*?"
    ),
    "profile_not_registered": "Parece que aún no has comenzado tu recorrido. Usa /start para dar tu primer paso.",
    "profile_title": "🛋️ *Tu rincón en El Diván de Diana*",
    "profile_points": "📌 *Puntos acumulados:* `{user_points}`",
    "profile_level": "🎯 *Nivel actual:* `{user_level}`",
    "profile_points_to_next_level": "📶 *Para el siguiente nivel:* `{points_needed}` más (Nivel `{next_level}` a partir de `{next_level_threshold}`)",
    "profile_max_level": "🌟 Has llegado al nivel más alto... y se nota. 😉",
    "profile_achievements_title": "🏅 *Logros desbloqueados*",
    "profile_no_achievements": "Aún no hay logros. Pero te tengo fe.",
    "profile_active_missions_title": "📋 *Tus desafíos activos*",
    "profile_no_active_missions": "Por ahora no hay desafíos, pero eso puede cambiar pronto. Mantente cerca.",
    "missions_title": "🎯 *Desafíos disponibles*",
    "missions_no_active": "No hay desafíos por el momento. Aprovecha para tomar aliento.",
    "mission_not_found": "Ese desafío no existe o ya expiró.",
    "mission_already_completed": "Ya lo completaste. Buen trabajo.",
    "mission_completed_success": "✅ ¡Desafío completado! Ganaste `{points_reward}` puntos.",
    "mission_level_up_bonus": "🚀 Subiste de nivel. Ahora estás en el nivel `{user_level}`. Las cosas se pondrán más interesantes.",
    "mission_achievement_unlocked": "\n🏆 Logro desbloqueado: *{achievement_name}*",
    "mission_completion_failed": "❌ No pudimos registrar este desafío. Revisa si ya lo hiciste antes o si aún está activo.",
    "reward_shop_title": "🎁 *Recompensas del Diván*",
    "reward_shop_empty": "Por ahora no hay recompensas disponibles. Pero pronto sí. 😉",
    "reward_not_found": "Esa recompensa ya no está aquí... o aún no está lista.",
    "reward_not_registered": "Tu perfil no está activo. Usa /start para comenzar *El Juego del Diván*.",
    "reward_out_of_stock": "Esa recompensa ya se fue. Las cosas buenas no esperan.",
    "reward_not_enough_points": "Te faltan `{required_points}` puntos. Ahora tienes `{user_points}`. Pero sigue... estás cerca.",
    "reward_purchase_success": "🎉 ¡Recompensa conseguida! Algo bonito está por llegar.",
    "reward_purchase_failed": "No pudimos procesar tu elección. Inténtalo más tarde.",

    # Mensajes de ranking (Unificados)
    "ranking_title": "🏆 *Tabla de Posiciones*",
    "ranking_entry": "#{rank}. @{username} - Puntos: `{points}`, Nivel: `{level}`",
    "no_ranking_data": "Aún no hay datos en el ranking. ¡Sé el primero en aparecer!",
    "back_to_main_menu": "Has regresado al centro del Diván. Elige por dónde seguir explorando.",

    # Botones
    "profile_achievements_button_text": "🏅 Mis Logros",
    "profile_active_missions_button_text": "🎯 Mis Desafíos",
    "back_to_profile_button_text": "← Volver a mi rincón",
    "view_all_missions_button_text": "Ver todos los desafíos",
    "back_to_missions_button_text": "← Volver a desafíos",
    "complete_mission_button_text": "✅ Completado",
    "confirm_purchase_button_text": "Canjear por `{cost}` puntos",
    "cancel_purchase_button_text": "❌ Cancelar",
    "back_to_rewards_button_text": "← Volver a recompensas",
    "prev_page_button_text": "← Anterior",
    "next_page_button_text": "Siguiente →",
    "back_to_main_menu_button_text": "← Volver al inicio",

    # Detalles
    "mission_details_text": (
        "🎯 *Desafío:* {mission_name}\n\n"
        "📖 *Descripción:* {mission_description}\n"
        "🎁 *Recompensa:* `{points_reward}` puntos\n"
        "⏱️ *Frecuencia:* `{mission_type}`"
    ),
    "reward_details_text": (
        "🎁 *Recompensa:* {reward_name}\n\n"
        "📌 *Descripción:* {reward_description}\n"
        "💰 *Costo:* `{reward_cost}` puntos\n"
        "{stock_info}"
    ),
    "reward_details_stock_info": "📦 *Disponibles:* `{stock_left}`",
    "reward_details_no_stock_info": "📦 *Disponibles:* ilimitadas",
    "reward_details_not_enough_points_alert": "💔 Te faltan puntos para esta recompensa. Necesitas `{required_points}`, tienes `{user_points}`. Sigue sumando, lo estás haciendo bien.",

    # Mensajes adicionales que eran mencionados en user_handlers.py
    "menu_missions_text": "Aquí están los desafíos que puedes emprender. ¡Cada uno te acerca más!",
    "menu_rewards_text": "¡Es hora de canjear tus puntos! Aquí tienes las recompensas disponibles:",
    "confirm_purchase_message": "¿Estás segur@ de que quieres canjear {reward_name} por {reward_cost} puntos?",
    "purchase_cancelled_message": "Compra cancelada. Puedes seguir explorando otras recompensas.",
    "unrecognized_command_text": "Comando no reconocido. Aquí está el menú principal:"
}
