# utils/messages.py

BOT_MESSAGES = {
    "start_welcome_new_user": (
        "🎉 ¡Hola, alma curiosa y bienvenida a tu rincón en El Diván de Diana! 🎉\n\n"
        "Aquí, cada interacción, cada risa y cada reflexión te acerca más al corazón de nuestra comunidad. "
        "Acumula puntos, sube en el diván, revela tus logros y déjate consentir con recompensas "
        "exclusivas. ¡Tu privacidad es nuestro secreto mejor guardado!\n\n"
        "¿Lista para descubrir tu lugar en el diván? Usa el menú de abajo para comenzar tu viaje."
    ),
    "start_welcome_returning_user": (
        "👋 ¡Hola de nuevo, querida alma! ¿Lista para una nueva sesión en El Diván?\n\n"
        "Tu lugar te espera. Usa el menú de abajo para revisar tus avances, misiones pendientes "
        "y las sorpresas que te aguardan."
    ),
    "profile_not_registered": "Parece que aún no te has acomodado en el diván. Por favor, usa /start para reservar tu lugar.",
    "profile_title": "🛋️ **Tu rincón en El Diván de Diana**", # Se concatenará con el nombre del usuario
    "profile_points": "✨ **Reflexiones acumuladas:** `{user_points}`", # "Puntos Acumulados"
    "profile_level": "🌟 **Tu Nivel de Consciencia:** `{user_level}`", # "Nivel Actual"
    "profile_points_to_next_level": "📈 **Próxima Iluminación:** `{points_needed}` más (Nivel `{next_level}` te espera con `{next_level_threshold}` reflexiones)", # "Puntos para el siguiente nivel"
    "profile_max_level": "✨ **¡Has alcanzado la Sabiduría Plena!**", # "Has alcanzado el nivel máximo"
    "profile_achievements_title": "🏆 **Tus Revelaciones Personales:**", # "Logros Desbloqueados"
    "profile_no_achievements": "Aún no has tenido ninguna revelación. ¡Sigue explorando tu interior para descubrirlas! 🚀",
    "profile_active_missions_title": "🎯 **Tus Tareas del Alma Pendientes:**", # "Misiones Activas"
    "profile_no_active_missions": "No tienes tareas pendientes para el alma. ¡Revisa la sección 'Misiones del Alma' para nuevas oportunidades de crecimiento! 🧘‍♀️",
    "missions_title": "🎯 **Misiones del Alma disponibles:**", # "Misiones disponibles"
    "missions_no_active": "No hay misiones del alma disponibles en este momento. ¡Vuelve pronto para seguir tu camino! 🧘‍♀️",
    "mission_not_found": "Misión del alma no encontrada o ya no está disponible en este momento.",
    "mission_already_completed": "Ya has completado esta misión del alma. ¡Tu consciencia ya absorbió esta lección!",
    "mission_completed_success": "✅ ¡Misión del alma '{mission_name}' completada! Has ganado `{points_reward}` reflexiones.",
    "mission_level_up_bonus": " ¡Felicidades, has subido al Nivel de Consciencia {user_level}!",
    "mission_achievement_unlocked": "\n🏆 ¡Has desbloqueado la revelación '{achievement_name}'!",
    "mission_completion_failed": "❌ No pudimos registrar tu misión del alma. Asegúrate de que esté activa o que no la hayas completado ya para este periodo.",
    "reward_shop_title": "🛍️ **Tu Tienda de Recompensas del Alma:**", # "Tienda de Recompensas"
    "reward_shop_empty": "La tienda de recompensas del alma está vacía. ¡Vuelve pronto para ver nuevas sorpresas! ✨",
    "reward_not_found": "Recompensa no encontrada o no disponible en este momento.",
    "reward_not_registered": "Usuario no encontrado. Por favor, inicia con /start para acceder a las recompensas.",
    "reward_out_of_stock": "¡Oops! Esa recompensa ha sido reclamada. Vuelve pronto para nuevas sorpresas.",
    "reward_not_enough_points": "No tienes suficientes reflexiones para esta recompensa. Necesitas `{required_points}` y tienes `{user_points}`.",
    "reward_purchase_success": "¡Felicidades! Has reclamado tu recompensa del alma. ¡Disfrútala!",
    "reward_purchase_failed": "Lo sentimos, no pudimos procesar tu compra. Intenta de nuevo más tarde.",
    "ranking_title": "🏆 **Tu Posición en El Diván (Top 10):**", # "Ranking de Usuarios"
    "ranking_no_users": "Aún no hay almas en el diván. ¡Sé la primera en compartir tu luz! 🚀",
    "back_to_main_menu": "¡Has regresado a tu espacio seguro en El Diván de Diana! Aquí puedes seguir navegando por las opciones principales de tu viaje de autodescubrimiento.",
    "profile_achievements_button_text": "Ver mis Revelaciones",
    "profile_active_missions_button_text": "Ver mis Tareas Pendientes",
    "back_to_profile_button_text": "🔙 Volver a mi Rincón",
    "view_all_missions_button_text": "Ver todas las Misiones del Alma",
    "back_to_missions_button_text": "🔙 Volver a Misiones del Alma",
    "complete_mission_button_text": "✅ He Cumplido esta Misión",
    "confirm_purchase_button_text": "Comprar por `{cost}` reflexiones",
    "cancel_purchase_button_text": "❌ Cancelar",
    "back_to_rewards_button_text": "🔙 Volver a la Tienda",
    "prev_page_button_text": "◀️ Anterior",
    "next_page_button_text": "Siguiente ▶️",
    "back_to_main_menu_button_text": "🔙 Volver al Diván Principal",
    # Mensajes de detalles
    "mission_details_text": (
        "🎯 **Misión del Alma: {mission_name}**\n\n"
        "📝 **Reflexión:** {mission_description}\n"
        "💰 **Recompensa por tu Esencia:** `{points_reward}` reflexiones\n"
        "⏰ **Frecuencia:** `{mission_type}`"
    ),
    "reward_details_text": (
        "🛍️ **Recompensa para tu Alma: {reward_name}**\n\n"
        "📝 **Detalle:** {reward_description}\n"
        "✨ **Costo de Auto-Cuidado:** `{reward_cost}` reflexiones\n"
        "{stock_info}"
    ),
    "reward_details_stock_info": "📦 **Unidades disponibles:** `{stock_left}`",
    "reward_details_no_stock_info": "📦 **Unidades disponibles:** Ilimitadas",
    "reward_details_not_enough_points_alert": "💔 ¡Lo siento, corazón! No tienes suficientes reflexiones para esta recompensa. Necesitas `{required_points}` y tienes `{user_points}`. ¡Sigue conectando con tu interior para acumular más!"
}
