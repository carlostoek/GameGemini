# bot.py
import asyncio
import logging
import datetime
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from sqlalchemy import select
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from database.setup import get_session, init_db # Ahora init_db y get_session
from database.models import Event
from config import Config
from handlers import user_handlers, admin_handlers

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    # --- CAMBIO DE OPTIMIZACIÓN DE DB AQUÍ ---
    # Inicializa la base de datos y el motor UNA SOLA VEZ
    await init_db()
    # Ahora, obtén la factoría de sesión una sola vez.
    # get_session() ya no llama a init_db(), sino que depende de _engine inicializado por init_db()
    Session = await get_session()
    # --- FIN CAMBIO DE OPTIMIZACIÓN ---

    bot = Bot(
        token=Config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
    )

    dp = Dispatcher(storage=MemoryStorage())

    # Registra los routers de handlers
    dp.include_router(user_handlers.router)
    dp.include_router(admin_handlers.router)

    # Middleware para pasar la sesión de la base de datos y la instancia del bot a los handlers
    def session_and_bot_middleware_factory(session_factory, bot_instance):
        async def session_and_bot_middleware(handler, event, data):
            async with session_factory() as session:
                data['session'] = session
                data['bot'] = bot_instance
                return await handler(event, data)
        return session_and_bot_middleware

    dp.message.outer_middleware(session_and_bot_middleware_factory(Session, bot))
    dp.callback_query.outer_middleware(session_and_bot_middleware_factory(Session, bot))

    # Configura y programa tareas con APScheduler
    scheduler = AsyncIOScheduler()

    async def check_active_events_and_notify(current_bot: Bot, current_session_factory):
        """
        Función programada para revisar eventos activos y notificar.
        """
        async with current_session_factory() as s:
            stmt = select(Event).where(Event.is_active == True)
            result = await s.execute(stmt)
            active_events = result.scalars().all()

            for event in active_events:
                # Desactiva eventos expirados
                if event.end_time and event.end_time < datetime.datetime.now():
                    event.is_active = False
                    await s.commit()
                    await current_bot.send_message(Config.CHANNEL_ID,
                                                   f"📢 **¡Evento Finalizado!**\n\n"
                                                   f"El evento '{event.name}' ha terminado.",
                                                   parse_mode=ParseMode.MARKDOWN)
                    logger.info(f"Event '{event.name}' deactivated.")
                # Aquí podrías añadir lógica para notificar sobre eventos en curso periódicamente
                # Por ejemplo, enviar recordatorios antes de que un evento termine.

    # Programa la revisión de eventos cada hora
    scheduler.add_job(check_active_events_and_notify, 'interval', hours=1, args=[bot, Session])
    scheduler.start()

    logger.info("Bot starting...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)
    logger.info("Bot stopped.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Error starting bot: {e}")

