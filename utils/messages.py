BOT_MESSAGES = {
    "start_welcome_new_user": (
        "🌙 Bienvenid@ al Diván de Diana...\n\n"
        "Aquí todo cuenta: lo que haces, lo que compartes, lo que descubres. Cada paso suma, cada interacción te acerca a recompensas pensadas para ti.\n\n"
        "¿Te animas a explorar a tu ritmo? Elige por dónde quieres empezar. El Diván ya está listo para ti."
    ),
    "start_welcome_returning_user": (
        "✨ Qué gusto tenerte de vuelta.\n\n"
        "Tu espacio está intacto, tus puntos siguen aquí... y las sorpresas no se han ido. ¿Le seguimos?"
    ),
    "profile_not_registered": "Parece que aún no estás dentro. Usa /start para activar tu perfil y comenzar el recorrido.",
    "profile_title": "🛋️ Tu rincón en El Diván de Diana",
    "profile_points": "📌 Tus puntos acumulados: `{user_points}`",
    "profile_level": "🎯 Nivel actual: `{user_level}`",
    "profile_points_to_next_level": "🚀 Próximo nivel en: `{points_needed}` puntos (Nivel `{next_level}` a partir de `{next_level_threshold}`)",
    "profile_max_level": "🌟 Has alcanzado el nivel máximo. Eso se nota. 😉",
    "profile_achievements_title": "🏅 Tus logros desbloqueados",
    "profile_no_achievements": "Aún no hay logros… pero eso puede cambiar muy pronto.",
    "profile_active_missions_title": "📋 Tus misiones activas",
    "profile_no_active_missions": "Por ahora no hay misiones activas, pero estate pendiente. Nunca sabes cuándo aparecerá algo nuevo.",
    "missions_title": "🎯 Misiones disponibles",
    "missions_no_active": "No hay nuevas misiones en este momento. Tómalo como una pausa... o una señal.",
    "mission_not_found": "Esa misión no existe o ya no está disponible.",
    "mission_already_completed": "Esa ya la completaste. Bien hecho.",
    "mission_completed_success": "✅ Misión completada: '{mission_name}'. Ganaste `{points_reward}` puntos.",
    "mission_level_up_bonus": "🎉 Subiste de nivel. Ahora estás en el nivel `{user_level}`. Se empieza a poner interesante.",
    "mission_achievement_unlocked": "\n🏆 Nuevo logro desbloqueado: '{achievement_name}'",
    "mission_completion_failed": "❌ Algo salió mal. Intenta de nuevo o revisa si ya la habías completado.",
    "reward_shop_title": "🎁 Tienda de recompensas",
    "reward_shop_empty": "La tienda está vacía por ahora. Pero no por mucho.",
    "reward_not_found": "No encontré esa recompensa. Tal vez ya se fue.",
    "reward_not_registered": "Tu perfil no está activo. Usa /start para comenzar.",
    "reward_out_of_stock": "Esa recompensa ya no está disponible. Lo bueno vuela.",
    "reward_not_enough_points": "Te faltan `{required_points}` puntos. Ahora tienes `{user_points}`. Sigue sumando y lo tendrás.",
    "reward_purchase_success": "🎉 Recompensa adquirida. ¡Disfrútala!",
    "reward_purchase_failed": "No pudimos procesar tu compra. Inténtalo más tarde.",
    "ranking_title": "🏆 Top 10 del Diván",
    "ranking_no_users": "Nadie se ha animado todavía. ¿Serás tú el primero?",
    "back_to_main_menu": "Volviste al inicio. Elige a dónde quieres ir desde aquí.",

    # Botones
    "profile_achievements_button_text": "Ver mis logros",
    "profile_active_missions_button_text": "Ver mis misiones",
    "back_to_profile_button_text": "← Volver a mi perfil",
    "view_all_missions_button_text": "Ver todas las misiones",
    "back_to_missions_button_text": "← Volver a misiones",
    "complete_mission_button_text": "✅ Misión completada",
    "confirm_purchase_button_text": "Canjear por `{cost}` puntos",
    "cancel_purchase_button_text": "Cancelar",
    "back_to_rewards_button_text": "← Volver a la tienda",
    "prev_page_button_text": "← Anterior",
    "next_page_button_text": "Siguiente →",
    "back_to_main_menu_button_text": "← Volver al menú principal",

    # Detalles
    "mission_details_text": (
        "📝 Misión: {mission_name}\n\n"
        "📖 Descripción: {mission_description}\n"
        "🎁 Recompensa: `{points_reward}` puntos\n"
        "⏱️ Frecuencia: `{mission_type}`"
    ),
    "reward_details_text": (
        "🎁 Recompensa: {reward_name}\n\n"
        "📌 Descripción: {reward_description}\n"
        "💰 Costo: `{reward_cost}` puntos\n"
        "{stock_info}"
    ),
    "reward_details_stock_info": "📦 Unidades disponibles: `{stock_left}`",
    "reward_details_no_stock_info": "📦 Unidades disponibles: ilimitadas",
    "reward_details_not_enough_points_alert": "No tienes suficientes puntos todavía. Necesitas `{required_points}` y tienes `{user_points}`. Pero vas por buen camino."
}
