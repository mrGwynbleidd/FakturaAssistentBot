#import libs
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
import asyncio

from aiogram.exceptions import TelegramBadRequest
from aiogram.utils.chat_action import ChatActionSender

from app.core.bot_engine import process_user_question
from app.bot.keyboards import main_menu_keyboard, language_keyboard
from app.bot.markdown_utils import safe_markdown_answer

from app.bot.texts import get_text

router = Router()

USER_LANGUAGES: dict[int, str] = {}

#return selected user language 
#otherwise bot_engine auto will detect language
def get_user_language(user_id: int) -> str:

    return USER_LANGUAGES.get(user_id, "ru")

#delete msg
async def delete_msg_safely(msg: Message) ->None:
    try:
        await msg.delete()
    except TelegramBadRequest:
        pass

#main menu
async def send_main_menu(message: Message, language: str) -> None:
    await message.answer(
        get_text("start", language),
        reply_markup=main_menu_keyboard(language),
    )


# ----------- /start -----------
@router.message(CommandStart())
async def start_handler(message: Message):
    
    language = get_user_language(message.from_user.id)

    await send_main_menu(message, language)

# ----------- /restart -----------
@router.message(Command("restart"))
async def restart_handler(msg: Message):
    
    user_id = msg.from_user.id

    USER_LANGUAGES.pop(user_id, None)

    language = "ru"

    await msg.answer(
        get_text("restart", "language"),
        reply_markup=main_menu_keyboard(language),
    )

# ----------- /help -----------
@router.message(Command("help"))
async def help_handler(msg: Message):

    language = get_user_language(msg.from_user.id)

    text = (
        "Как пользоваться ботом:\n\n"
        "1. Просто напишите вопрос, например:\n"
        "   «Как зарегистрироваться?»\n"
        "   «Не могу войти в аккаунт»\n"
        "   «Как создать счет-фактуру?»\n\n"
        "2. Бот найдёт подходящую инструкцию в базе знаний.\n\n"
        "3. Если точного ответа нет, вопрос будет сохраннён для проверки"
    )

    if language == "uz":
        text = (
            "Botdan foydalanish:\n\n"
            "1. Savolingizni yozing, masalan:\n"
            "   «Qanday ro‘yxatdan o‘taman?»\n"
            "   «Akkauntga kira olmayapman»\n"
            "   «Hisob-fakturani qanday yarataman?»\n\n"
            "2. Bot bilimlar bazasidan mos yo‘riqnomani topadi.\n\n"
            "3. Agar aniq javob bo‘lmasa, savol tekshiruvga saqlanadi."
            )

    elif language == "en":
        text = (
            "How to use the bot:\n\n"
            "1. Just write your question, for example:\n"
            "   “How can I register?”\n"
            "   “I cannot log into my account”\n"
            "   “How to create an invoice?”\n\n"
            "2. The bot will search the knowledge base.\n\n"
            "3. If there is no exact answer, the question will be saved for review."
        )

    await msg.answer(text, reply_markup=main_menu_keyboard(language))

# # ----------- Main buttons -----------

# Ask question
@router.message(F.text.in_
                (
                    ["❓ Задать вопрос", "❓ Savol berish",
                     "❓ Ask a question",
                    ])
            )
async def ask_question_button(msg: Message):

    language = get_user_language(msg.from_user.id)

    await msg.answer(
        get_text("ask_question", language),
        reply_markup=main_menu_keyboard(language),
    )


# Select Language
@router.message(F.text.in_(
        [
            "🌐 Выбрать язык",
            "🌐 Tilni tanlash",
            "🌐 Choose language",
        ]
    )
    )
async def choose_language_button(msg: Message):

    language = get_user_language(msg.from_user.id)

    await msg.answer(
            get_text("choose_language", language),
            reply_markup=language_keyboard(language),
    )

# Back Button
@router.message(F.text.in_(
        [
            "⬅️ Назад",
            "⬅️ Orqaga",
            "⬅️ Back",
        ]
    ))
async def back_button(msg: Message):

    language = get_user_language(msg.from_user.id)

    await msg.answer(
        get_text("main_menu", language),
        reply_markup=main_menu_keyboard(language),
    )

# Bot Features
@router.message(F.text.in_(
        [
            "📚 Возможности бота",
            "📚 Bot imkoniyatlari",
            "📚 Bot features",
        ]
    ))
async def features_handler(message: Message):
    
    language = get_user_language(message.from_user.id)

    await message.answer(
        get_text("features", language),
        reply_markup=main_menu_keyboard(language),
    )

# Support
@router.message(F.text.in_(
        [
            "🆘 Поддержка",
            "🆘 Yordam",
            "🆘 Support",
        ]
    ))
async def support_handler(msg: Message):
    
    language = get_user_language(msg.from_user.id)

    await msg.answer(
        get_text("support", language),
        reply_markup=main_menu_keyboard(language),
    )

# Restart Button
@router.message(
    F.text.in_(
        [
            "🔄 Перезапустить",
            "🔄 Qayta boshlash",
            "🔄 Restart",
        ]
    )
)
async def restart_button_handler(message: Message):
    """
    Кнопка перезапуска.
    """

    await restart_handler(message)


# Language Selection

@router.message(F.text == "🇷🇺 Русский")
async def set_ru_language(msg: Message):
    USER_LANGUAGES[msg.from_user.id] = "ru"

    await msg.answer(
        get_text("language_set_ru", "ru"),
        reply_markup=main_menu_keyboard("ru"),
    )

@router.message(F.text == "🇺🇿 O‘zbekcha")
async def set_uz_language(message: Message):
    USER_LANGUAGES[message.from_user.id] = "uz"

    await message.answer(
        get_text("language_set_uz", "uz"),
        reply_markup=main_menu_keyboard("uz"),
    )


@router.message(F.text == "🇬🇧 English") ###
async def set_en_language(message: Message):
    USER_LANGUAGES[message.from_user.id] = "en"

    await message.answer(
        get_text("language_set_en", "en"),
        reply_markup=main_menu_keyboard("en"),
    )

# User Questions

@router.message(F.text)
async def question_handler(msg: Message):

    #get user question
    user_question = msg.text.strip()
    #his id
    user_id = msg.from_user.id
    #language
    language = get_user_language(user_id)

    # if question is empty
    if not user_question:
        await msg.answer(
            get_text("empty_question", language),
            reply_markup=main_menu_keyboard(language),
        )
        return

    #print searching text    
    search_message = await msg.answer(
        get_text("searching", language),
        reply_markup=main_menu_keyboard(language)
    )

    try:
        async with ChatActionSender.typing(
            bot=msg.bot,
            chat_id=msg.chat.id,
        ):
            result = await asyncio.to_thread(
                process_user_question,
                user_question,
                True,
                True,
                language
            )
    finally:
        await delete_msg_safely(search_message)

    answer = result.get("answer", get_text("error_answer", language))
   
   
    #    async with ChatActionSender.typing(bot=msg.bot, chat_id=msg.chat.id):
    #     searching_msg = await msg.answer(get_text("searching", language))
    #     result = await asyncio.get_event_loop().run_in_executor(
    #         None,
    #         lambda: process_user_question(question, forced_language=language),
    #     )
    #     await delete_msg_safely(searching_msg)

    # answer = result.get("answer", get_text("error_answer", language))
    # await msg.answer(answer, reply_markup=main_menu_keyboard(language))



    ### Info for testing

    sources = result.get("sources", [])
    sent_to_review = result.get("sent_to_review")
    review_case_id = result.get("review_case_id")

    final_text = answer

    if not isinstance(sources, list):
        sources = []

    if sources:
        unique_sources: list[str] = []

        for source_item in sources:
            if isinstance(source_item, dict):
                source_name = str(source_item.get("source", "unknown"))
            else:
                source_name = str(source_item)

            if source_name not in unique_sources:
                unique_sources.append(source_name)

        sources_text = "\n".join(
            f"— {source_name}" for source_name in unique_sources[:3]
        )

        final_text += f"\n\n{get_text('sources', language)}\n{sources_text}"



    if sent_to_review:
        final_text += (
            f"\n\n{get_text('saved_review', language)} {review_case_id}"
        )

    #####

    final_text = safe_markdown_answer(final_text)

    try:
        await msg.answer(
            final_text,
            reply_markup=main_menu_keyboard(language),
            parse_mode="Markdown",
        )
    except Exception:
        # fallback: отправить без форматирования если Markdown сломан
        import re as _re
        plain = _re.sub(r'[*_`]', '', final_text)
        await msg.answer(plain, reply_markup=main_menu_keyboard(language))


from aiogram.types import PhotoSize
from app.core.bot_engine import process_user_image

@router.message(F.photo)
async def photo_handler(msg: Message):

    user_id = msg.from_user.id
    language = get_user_language(user_id)
    photo: PhotoSize = msg.photo[-1]
    caption: str = msg.caption or ""

    search_message = await msg.answer(
        get_text("searching", language),
        reply_markup=main_menu_keyboard(language),
    )

    try:
        async with ChatActionSender.typing(bot=msg.bot, chat_id=msg.chat.id):
            file = await msg.bot.get_file(photo.file_id)
            file_bytes = await msg.bot.download_file(file.file_path)
            image_bytes: bytes = file_bytes.read()

            result = await asyncio.to_thread(
                process_user_image,
                image_bytes,
                caption,
                True,
                True,
                language,
            )
    finally:
        await delete_msg_safely(search_message)

    answer = result.get("answer", get_text("error_answer", language))
    sources = result.get("sources", [])
    sent_to_review = result.get("sent_to_review")
    review_case_id = result.get("review_case_id")

    final_text = answer

    if sources and isinstance(sources, list):
        unique_sources: list[str] = []
        for s in sources:
            name = str(s.get("source", "unknown")) if isinstance(s, dict) else str(s)
            if name not in unique_sources:
                unique_sources.append(name)
        sources_text = "\n".join(f"— {s}" for s in unique_sources[:3])
        final_text += f"\n\n{get_text('sources', language)}\n{sources_text}"

    if sent_to_review:
        final_text += f"\n\n{get_text('saved_review', language)} {review_case_id}"

    final_text = safe_markdown_answer(final_text)

    try:
        await msg.answer(
            final_text,
            reply_markup=main_menu_keyboard(language),
            parse_mode="Markdown",
        )
    except Exception:
        import re as _re
        plain = _re.sub(r'[*_`]', '', final_text)
        await msg.answer(plain, reply_markup=main_menu_keyboard(language))

