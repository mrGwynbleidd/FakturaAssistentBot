
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message

from app.admin.services.read_only_service import is_read_only_for_chat
from app.bot.photo_collector import save_group_photo

class ReadOnlyMiddleware(BaseMiddleware):
    async def __call__(self, handler: Callable[[Message, dict[str, Any]], Awaitable[Any]], event: Message, data: dict[str, Any],)->Any:
        
        if not isinstance(event, Message):
            return await handler(event, data)
        
        if not is_read_only_for_chat(event.chat.id):
            return await handler(event, data)
        
        if event.photo:
            print("PHOTO DETECTED IN READ ONLY:", event.chat.id, event.message_id)
            saved_path = await save_group_photo(event)
            print("PHOTO SAVED TO:", saved_path)
            await save_group_photo(event)
        
        return None
