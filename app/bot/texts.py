TEXTS = {
    "ru": {
        "start": (
            "Здравствуйте! Я Faktura Helper Bot.\n\n"
            "Я могу помочь вам найти информацию по Faktura.uz:\n"
            "— по PDF-инструкциям;\n"
            "— по базе знаний;\n"
            "— по API-данным Faktura, если они подключены;\n"
            "— на русском, узбекском и английском языках.\n\n"
            "Напишите вопрос или выберите действие ниже."
        ),
        "restart": (
            "Интерфейс перезапущен.\n\n"
            "Вы можете заново выбрать язык или сразу написать вопрос."
        ),
        "ask_question": "Напишите ваш вопрос по Faktura.uz одним сообщением.",
        "choose_language": "Выберите язык:",
        "language_set_ru": "Язык установлен: русский.",
        "language_set_uz": "Til tanlandi: o‘zbekcha.",
        "language_set_en": "Language selected: English.",
        "main_menu": "Главное меню.",
        "features": (
            "Что умеет бот:\n\n"
            "— отвечать на вопросы по Faktura.uz;\n"
            "— искать информацию в PDF-инструкциях;\n"
            "— использовать ChromaDB для поиска по смыслу;\n"
            "— работать с русским, узбекским и английским языками;\n"
            "— сохранять вопросы и ответы в CSV;\n"
            "— отправлять сложные вопросы на проверку;\n"
            "— получать данные через Faktura API."
        ),
        "support": (
            "Если бот не смог ответить точно, вопрос будет сохранён для проверки.\n\n"
            "Поддержка Faktura.uz:\n"
            "+998 71 200 00 13"
        ),
        "empty_question": "Пожалуйста, напишите вопрос.",
        "searching": "Ищу информацию в базе знаний...",
        "sources": "Источники:",
        "saved_review": "Ваш вопрос сохранён для дополнительной проверки специалистом.",
        "case_id": "ID обращения:",
        "error_answer": "Не удалось сформировать ответ.",
    },

    "uz": {
        "start": (
            "Assalomu alaykum! Men Faktura Helper Botman.\n\n"
            "Men sizga Faktura.uz bo‘yicha ma’lumot topishda yordam beraman:\n"
            "— PDF yo‘riqnomalar bo‘yicha;\n"
            "— bilimlar bazasi bo‘yicha;\n"
            "— ulangan bo‘lsa, Faktura API ma’lumotlari bo‘yicha;\n"
            "— rus, o‘zbek va ingliz tillarida.\n\n"
            "Savolingizni yozing yoki quyidagi menyudan foydalaning."
        ),
        "restart": (
            "Interfeys qayta ishga tushirildi.\n\n"
            "Tilni qayta tanlashingiz yoki darhol savol yozishingiz mumkin."
        ),
        "ask_question": "Faktura.uz bo‘yicha savolingizni bitta xabar qilib yozing.",
        "choose_language": "Tilni tanlang:",
        "language_set_ru": "Язык установлен: русский.",
        "language_set_uz": "Til tanlandi: o‘zbekcha.",
        "language_set_en": "Language selected: English.",
        "main_menu": "Asosiy menyu.",
        "features": (
            "Bot imkoniyatlari:\n\n"
            "— Faktura.uz bo‘yicha savollarga javob beradi;\n"
            "— PDF yo‘riqnomalardan ma’lumot qidiradi;\n"
            "— ma’noga ko‘ra qidirish uchun ChromaDB ishlatadi;\n"
            "— rus, o‘zbek va ingliz tillarida ishlaydi;\n"
            "— savol va javoblarni CSV faylga saqlaydi;\n"
            "— murakkab savollarni tekshiruvga yuboradi;\n"
            "— Faktura API orqali ma’lumot oladi."
        ),
        "support": (
            "Agar bot aniq javob bera olmasa, savol tekshiruv uchun saqlanadi.\n\n"
            "Faktura.uz qo‘llab-quvvatlash xizmati:\n"
            "+998 71 200 00 13"
        ),
        "empty_question": "Iltimos, savol yozing.",
        "searching": "Bilimlar bazasidan ma’lumot qidiryapman...",
        "sources": "Manbalar:",
        "saved_review": "Savolingiz mutaxassis tekshiruvi uchun saqlandi.",
        "case_id": "Murojaat ID:",
        "error_answer": "Javobni shakllantirib bo‘lmadi.",
    },

    "en": {
        "start": (
            "Hello! I am Faktura Helper Bot.\n\n"
            "I can help you find information about Faktura.uz:\n"
            "— from PDF instructions;\n"
            "— from the knowledge base;\n"
            "— from Faktura API data if connected;\n"
            "— in Russian, Uzbek and English.\n\n"
            "Write your question or choose an action below."
        ),
        "restart": (
            "The interface has been restarted.\n\n"
            "You can choose the language again or write your question."
        ),
        "ask_question": "Write your Faktura.uz question in one message.",
        "choose_language": "Choose language:",
        "language_set_ru": "Язык установлен: русский.",
        "language_set_uz": "Til tanlandi: o‘zbekcha.",
        "language_set_en": "Language selected: English.",
        "main_menu": "Main menu.",
        "features": (
            "Bot features:\n\n"
            "— answers questions about Faktura.uz;\n"
            "— searches PDF instructions;\n"
            "— uses ChromaDB for semantic search;\n"
            "— works in Russian, Uzbek and English;\n"
            "— saves questions and answers to CSV;\n"
            "— sends difficult questions for review;\n"
            "— gets data through Faktura API."
        ),
        "support": (
            "If the bot cannot answer accurately, the question will be saved for review.\n\n"
            "Faktura.uz support:\n"
            "+998 71 200 00 13"
        ),
        "empty_question": "Please write a question.",
        "searching": "Searching the knowledge base...",
        "sources": "Sources:",
        "saved_review": "Your question has been saved for additional specialist review.",
        "case_id": "Case ID:",
        "error_answer": "Could not generate an answer.",
    },
}


def get_text(key: str, language: str = "ru") -> str:
    """
    Возвращает текст интерфейса на выбранном языке.
    """

    if language not in TEXTS:
        language = "ru"

    return TEXTS[language].get(key, TEXTS["ru"].get(key, key))
