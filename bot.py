import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage # Consider using Redis for production
from sqlalchemy.ext.asyncio import AsyncSession
from database.setup import get_session, init_db
from config import Config
from handlers import user_handlers, admin_handlers
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import datetime
from sqlalchemy import select
from database.models import Event

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    # Initialize database
    engine = await init_db()
    Session = await get_session()

    bot = Bot(token=Config.BOT_TOKEN, parse_mode=ParseMode.MARKDOWN) # Changed to Markdown for easier formatting
    dp = Dispatcher(storage=MemoryStorage())

    # Register handlers
    dp.include_router(user_handlers.router)
    dp.include_router(admin_handlers.router)

    # Middleware to pass the database session and bot instance to handlers
    @dp.callback_query()
    @dp.message()
    async def session_and_bot_middleware(event, handler, *args, **kwargs):
        async with Session() as session:
            kwargs['session'] = session
            kwargs['bot'] = bot # Pass bot instance to handlers for sending messages
            return await handler(event, *args, **kwargs)

    # Schedule tasks
    scheduler = AsyncIOScheduler()

    async def check_active_events_and_notify(current_bot: Bot, current_session_factory):
        async with current_session_factory() as s:
            stmt = select(Event).where(Event.is_active == True)
            result = await s.execute(stmt)
            active_events = result.scalars().all()

            for event in active_events:
                # Deactivate expired events
                if event.end_time and event.end_time < datetime.datetime.now():
                    event.is_active = False
                    await s.commit()
                    await current_bot.send_message(Config.CHANNEL_ID,
                                                   f"📢 **¡Evento Finalizado!**\n\n"
                                                   f"El evento '{event.name}' ha terminado.",
                                                   parse_mode="Markdown")
                    logger.info(f"Event '{event.name}' deactivated.")
                # You could add logic here to notify about ongoing events periodically
                # For this example, notifications are only sent on activation/deactivation

    # Schedule to run every hour to check events
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

