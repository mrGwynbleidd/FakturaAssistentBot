import os
os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "1"

import asyncio

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage  # добавь

from app.config import TELEGRAM_BOT_TOKEN
from app.bot.handlers import router
from app.bot.admin_handlers import router as admin_router  # добавь


async def main():
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())  # storage нужен для FSM

    dp.include_router(admin_router)  # ВАЖНО: admin раньше обычного router
    dp.include_router(router)

    print("Faktura Assistant Bot is running...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())