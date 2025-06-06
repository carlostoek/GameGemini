import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from sqlalchemy.ext.asyncio import AsyncSession
from database.setup import get_session, init_db
from config import Config
from handlers import user_handlers, admin_handlers
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    # Initialize database
    engine = await init_db()
    Session = await get_session()

    bot = Bot(token=Config.BOT_TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher(storage=MemoryStorage()) # Use MemoryStorage for simplicity; consider Redis for production

    # Register handlers
    dp.include_router(user_handlers.router)
    dp.include_router(admin_handlers.router)

    # Middleware to pass the database session to handlers
    @dp.callback_query()
    @dp.message()
    async def session_middleware(event, handler, *args, **kwargs):
        async with Session() as session:
            kwargs['session'] = session
            kwargs['bot'] = bot # Pass bot instance to handlers for sending messages
            return await handler(event, *args, **kwargs)

    # Schedule tasks (e.g., daily/weekly mission resets, event checks)
    scheduler = AsyncIOScheduler()

    # Example: Check for active events every minute
    # In a real scenario, you might want to fetch events from DB and schedule them directly
    # Or have a simpler flag in DB
    # async def check_active_events(bot: Bot, session: AsyncSession):
    #     async with Session() as s:
    #         # Logic to check events and notify channel if needed
    #         # Example: stmt = select(Event).where(Event.is_active == True, Event.end_time > datetime.datetime.now())
    #         # result = await s.execute(stmt)
    #         # active_events = result.scalars().all()
    #         # ... notify logic ...
    #     logger.info("Checking for active events...")

    # scheduler.add_job(check_active_events, 'interval', minutes=1, args=[bot, Session])

    # For daily mission resets (can be integrated into MissionService more robustly)
    # For now, relying on last_daily_mission_reset in User model and check in service

    scheduler.start()

    logger.info("Bot starting...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)
    logger.info("Bot stopped.")


if __name__ == "__main__":
    asyncio.run(main())
    
