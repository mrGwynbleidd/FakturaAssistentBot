#create keyboard menu for bot

#import libs
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

#main menu
def main_menu_keyboard(language: str = "ru") -> ReplyKeyboardMarkup:
    
    #main menu in uzbek
    if language == "uz":
        keyboard = [
            [
                KeyboardButton(text="❓ Savol berish"),
                KeyboardButton(text="🌐 Tilni tanlash"),
            ],
            [
                KeyboardButton(text="📚 Bot imkoniyatlari"),
                KeyboardButton(text="🆘 Yordam"),
            ],
            [
                KeyboardButton(text="🔄 Qayta boshlash"),
            ],
        ]

        placeholder = "Faktura.uz bo‘yicha savolingizni yozing..."

    #in english
    elif language == "en":
            keyboard = [
                 [
                      KeyboardButton(text="❓ Ask a question"),
                      KeyboardButton(text="🌐 Choose language"),
                 ],
                [
                KeyboardButton(text="📚 Bot features"),
                KeyboardButton(text="🆘 Support"),
                ],
                [
                KeyboardButton(text="🔄 Restart"),
                ],
            ]

            placeholder = "Write your question about Faktura.uz..."

    #by default russian
    else:           
        keyboard =[
            [
                KeyboardButton(text="❓ Задать вопрос"),
                KeyboardButton(text="🌐 Выбрать язык"),
            ],
            [
                KeyboardButton(text="📚 Возможности бота"),
                KeyboardButton(text="🆘 Поддержка"),
            ],
            [
                KeyboardButton(text="🔄 Перезапустить"),
            ],
        ]

        #msg while answer is creating
        return ReplyKeyboardMarkup(
            keyboard=keyboard,
            resize_keyboard=True,
            input_field_placeholder="Напишите ваш вопрос по Faktura.uz...",
        )

#language selector
def language_keyboard(language: str = "ru") -> ReplyKeyboardMarkup:
    
    if language == "uz":
        back_text = "⬅️ Orqaga"
    elif language == "en":
        back_text = "⬅️ Back"
    else:
        back_text = "⬅️ Назад"

    keyboard = [
        [
            KeyboardButton(text="🇷🇺 Русский"),
            KeyboardButton(text="🇺🇿 O‘zbekcha"),
            KeyboardButton(text="🇬🇧 English"),
        ],
        [
            KeyboardButton(text=back_text),
        ],
    ]

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )
