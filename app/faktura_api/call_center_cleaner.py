#cleans raw call center ticket text by removing telegram support bot noise, pii, and template messages
#used in call_center_api.build_qa and import_call_center_2approved.import_callcenter_approved

import re

#normalizes apostrophe variants to a standard single quote
_APOSTROPHE_RE = re.compile(r"['''ʼʼ`]")

def _norm(text: str) -> str:
    return _APOSTROPHE_RE.sub("'", text)


#noise phrases that appear in ticket titles and user messages from the support telegram bot
_QUESTION_NOISE_ORIG: list[str] = [
    "Личное сообщение Telegram",
    "Operator",
    "Создать заявку",
    "Murojat yaratish",
    "API / интеграция",
    "API / Integratsiya",
    "ЭСФ / отправка документов",
    "Elektron hisob-faktura / hujjatlarni yuborish",
    "Проблема со входом",
    "Tizimga kirishda muammo",
    "Другое",
    "Boshqa",
    "Tizim xatosi",
    "Системная ошибка",
    "Синхронизация",
    "Sinxronizatsiya",
    "English",
    "/start",
    "Forwarded from",
    "Muammoingizni tezroq hal qilish",
    "Murojat turini tanlang",
]

#boilerplate phrases from the support bot that appear in agent answer messages
_ANSWER_TEMPLATES_ORIG: list[str] = [
    "Выберите язык! Tilni tanlang!",
    "Tilni tanlang!",
    "Выберите язык!",
    "Для более быстрого решения вопроса выберите нужный раздел ниже",
    "Выберите тип обращения:",
    "Выберите тип обращения",
    "Введите ИНН/ПИНФЛ компании:",
    "Введите ИНН/ПИНФЛ компании",
    "Kompaniyaning TIN (INN)/JSHIR (PINFL) raqamini kiriting",
    "Опишите проблему максимально подробно. Укажите:",
    "Опишите проблему максимально подробно",
    "Muammoni iloji boricha batafsil tavsiflang",
    "Faktura.uz qo'llab-quvvatlash xizmatiga murojaat qilganingiz uchun rahmat",
    "Rahmat, murojaat qilganingiz uchun!",
    "Rahmat, murojaat qilganingiz uchun",
    "Agar muammoingiz hal qilingan bo'lsa",
    "Ваш вопрос передан оператору",
    "Operator siz bilan yaqin vaqt ichida bog'lanadi",
    "Operator uchun mavjud bo'lgan noyob ariza identifikatori",
    "Sizning ariza raqamingiz:",
    "Sizning ariza raqamingiz",
    "Xizmat sifatini baholang",
    "Yaxshi kun tilaymiz!",
    "Yaxshi kun tilaymiz",
    "{hde-reply-to:",
    "Ko'rsating:",
    "Ko'rsating",
    "Muammoingizni tezroq hal qilish uchun quyidagi kerakli bo'limni tanlang",
    "Muammoingizni tezroq hal qilish",
    "Murojat turini tanlang:",
    "Murojat turini tanlang",
    ". Ko'rsating:",
    "• что именно не работает",
    "• в каком разделе возникла ошибка",
    "• какие действия выполнялись до ошибки",
    "• текст ошибки (если есть)",
    "• xatodan oldin qanday harakatlar",
    "• xato matni (mavjud bo'lsa)",
    "ИНН должен состоять ровно из 9 цифр",
    "Описание слишком короткое",
]

#additional boilerplate templates for answers
_ANSWER_EXTRA_TEMPLATES: list[str] = [
    "Tavsif juda qisqa. Iltimos, muammoni batafsilroq tasvirlab bering",
    "Tavsif juda qisqa",
    "Soliq to'lovchining identifikatsiya raqami (TIN) to'liq 9 ta raqamdan iborat bo'lishi kerak. Iltimos, qayta urinib ko'ring",
    "Здравствуйте! Вы обратились в службу поддержки Faktura.uz",
    "Assalomu alaykum! Siz Faktura.uz qo'llab-quvvatlash xizmatiga murojaat qildingiz",
    "Благодарим что обратились в службу поддержки Faktura.uz",
    "Время работы службы поддержки",
    "Спасибо за обращение! Ваш номер заявки",
    "Уникальный номер заявки доступный оператору",
    "Оператор подключится к вам в ближайшее время",
    "Оператор подключится в ближайшее время",
    "Пожалуйста, попробуйте снова",
    "Пожалуйста, опишите проблему подробнее",
    "yuz berdi bajarildan",
    "yuz berdi bajarilgan",
    "Ваш номер заявки",
    "Assalomu alaykum",
    "Ассалому алайкум",
    "Здравствуйте",
]

#regex patterns for removing personal/technical identifiers from text
_INN_PATTERN = re.compile(r'\b\d{9}\b')
_HASH_PATTERN = re.compile(r'\b[a-f0-9]{24,}\b')
_IP_PATTERN = re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b')
_PHONE_PATTERN = re.compile(r'\+?998\d{9}')
_TICKET_ID_PATTERN = re.compile(r'FUZ-\d+/\d+')
_TICKET_NUM_PATTERN = re.compile(r'(заявки|raqamingiz|ariza)\s+\d+', re.IGNORECASE)
_TICKET_ARTIFACT = re.compile(r'\b\d{3,6}\}\s*')
_URL_PATTERN = re.compile(r'https?://\S+')
_EMOJI_PATTERN = re.compile(
    '[\U0001F300-\U0001F9FF\U00002700-\U000027BF\U0001FA00-\U0001FA6F'
    '\U0001FA70-\U0001FAFF\U00002600-\U000026FF\U0000FE0F\U0000200D]+'
)
_LEADING_GARBAGE = re.compile(r'^[\s\d\.:\-,;•?!\(\)]+')


#removes all given phrases from text after normalizing apostrophes
#used in clean_question and clean_answer
def _remove_all(text: str, phrases: list[str]) -> str:
    text_n = _norm(text)
    for phrase in phrases:
        phrase_n = _norm(phrase)
        text_n = text_n.replace(phrase_n, " ")
    return text_n


#removes noise phrases, pii (inn, phone, ip, hash, url, emoji), and leading garbage from question text
#returns cleaned question string
#used in call_center_api.build_qa and import_call_center_2approved
def clean_question(raw: str) -> str:
    text = raw or ""
    text = _remove_all(text, _QUESTION_NOISE_ORIG)
    text = _INN_PATTERN.sub(" ", text)
    text = _HASH_PATTERN.sub(" ", text)
    text = _IP_PATTERN.sub(" ", text)
    text = _PHONE_PATTERN.sub(" ", text)
    text = _TICKET_ID_PATTERN.sub(" ", text)
    text = _URL_PATTERN.sub(" ", text)
    text = _EMOJI_PATTERN.sub(" ", text)
    text = _LEADING_GARBAGE.sub("", text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


#removes bot template phrases, ticket ids, urls, and leading garbage from answer text
#returns cleaned answer string
#used in call_center_api.build_qa and import_call_center_2approved
def clean_answer(raw: str) -> str:
    text = raw or ""
    text = _remove_all(text, _ANSWER_TEMPLATES_ORIG)
    text = _remove_all(text, _ANSWER_EXTRA_TEMPLATES)
    text = _TICKET_ID_PATTERN.sub(" ", text)
    text = _TICKET_NUM_PATTERN.sub(" ", text)
    text = _TICKET_ARTIFACT.sub(" ", text)
    text = _URL_PATTERN.sub(" ", text)
    text = _EMOJI_PATTERN.sub(" ", text)
    text = _LEADING_GARBAGE.sub("", text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


#returns true if both question and answer meet minimum length requirements
#used in call_center_api.build_qa and import_call_center_2approved to filter out low-quality pairs
def is_quality_pair(question: str, answer: str,
                    min_q: int = 20, min_a: int = 40) -> bool:
    return len(question) >= min_q and len(answer) >= min_a
