import logging
import os
import asyncio
import traceback

# Silence noisy third-party libraries
logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
logging.getLogger("transformers").setLevel(logging.WARNING)
logging.getLogger("chromadb").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("aiogram").setLevel(logging.WARNING)

os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "1"

# Clean, minimal log format
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.session.aiohttp import AiohttpSession




async def main():
    logger.info("🚀 Бот запускается...")

    try:
        from app.config import TELEGRAM_BOT_TOKEN, HF_TOKEN

        if HF_TOKEN:
            os.environ["HF_TOKEN"] = HF_TOKEN

        from app.bot.handlers import router as user_router
        from app.admin.admin_router import admin_router
        from app.bot.group_handlers import group_router
        from app.bot.read_only_middleware import ReadOnlyMiddleware

        user_router.message.middleware(ReadOnlyMiddleware())

        session = AiohttpSession()
        bot = Bot(token=TELEGRAM_BOT_TOKEN, session=session)
        dp = Dispatcher(storage=MemoryStorage())

        dp.include_router(admin_router)
        dp.include_router(group_router)   # group Q&A learning — before main router
        dp.include_router(user_router)

        logger.info("✅ Бот запущен и ждёт сообщений")
        await dp.start_polling(bot)

    except Exception as e:
        logger.error(f"💥 CRASH: {e}")
        logger.error(traceback.format_exc())
        raise


if __name__ == "__main__":
    asyncio.run(main())