#entry point of the bot — configures logging, creates bot and dispatcher, registers all routers, starts polling

import logging
import os
import asyncio
import traceback

#configure logging before any getLogger calls — format and level for all loggers
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%H:%M:%S",
)

#silence noisy third-party libraries to reduce console output
logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
logging.getLogger("transformers").setLevel(logging.WARNING)
logging.getLogger("chromadb").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("aiogram").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("google").setLevel(logging.WARNING)

#keep bot-specific loggers at INFO so pipeline actions are visible in console
logging.getLogger("bot").setLevel(logging.INFO)
logging.getLogger("bot.engine").setLevel(logging.INFO)
logging.getLogger("bot.retriever").setLevel(logging.INFO)

#disable implicit huggingface hub token warnings
os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "1"

logger = logging.getLogger(__name__)

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.session.aiohttp import AiohttpSession


#initializes and starts the telegram bot, registers all routers, begins polling
async def main():
    logger.info("Бот запускается...")

    try:
        from app.config import TELEGRAM_BOT_TOKEN, HF_TOKEN

        #set hf token in environment if provided
        if HF_TOKEN:
            os.environ["HF_TOKEN"] = HF_TOKEN

        #import all routers
        from app.bot.handlers import router as user_router
        from app.admin.admin_router import admin_router
        from app.bot.group_handlers import group_router
        from app.bot.user_sync_roaming_handler import router as sync_router

        session = AiohttpSession()
        bot = Bot(token=TELEGRAM_BOT_TOKEN, session=session)
        dp = Dispatcher(storage=MemoryStorage())

        #register routers — order matters: admin and group before main user router
        dp.include_router(admin_router)
        dp.include_router(group_router)   #group Q&A — before main router
        dp.include_router(sync_router)    #sync FSM — before main text handler
        dp.include_router(user_router)

        logger.info("Бот запущен и ждёт сообщений")
        await dp.start_polling(bot)

    except Exception as e:
        logger.error(f"CRASH: {e}")
        logger.error(traceback.format_exc())
        raise


if __name__ == "__main__":
    asyncio.run(main())
