import os
os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "1"

import asyncio
import traceback
import logging

# Подробные логи
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.session.aiohttp import AiohttpSession


async def main():
    logger.info("=== BOT STARTING ===")

    try:
        logger.info("Importing config...")
        from app.config import TELEGRAM_BOT_TOKEN, HF_TOKEN
        logger.info("Config OK")

        if HF_TOKEN:
            os.environ["HF_TOKEN"] = HF_TOKEN
            logger.info("HF_TOKEN set")

        logger.info("Importing routers...")
        from app.bot.handlers import router
        from app.bot.admin_handlers import router as admin_router
        logger.info("Routers OK")

        logger.info("Creating bot...")
        session = AiohttpSession()
        bot = Bot(token=TELEGRAM_BOT_TOKEN, session=session)
        dp = Dispatcher(storage=MemoryStorage())

        dp.include_router(admin_router)
        dp.include_router(router)
        logger.info("Bot created OK")

        logger.info("=== BOT IS RUNNING ===")
        await dp.start_polling(bot)

    except Exception as e:
        logger.error("=== CRASH ===")
        logger.error(f"Error: {e}")
        logger.error(traceback.format_exc())
        raise


if __name__ == "__main__":
    asyncio.run(main())