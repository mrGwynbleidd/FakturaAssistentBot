
STANDARD_FIELDS = [
    "ticket_id",
    "created_at",
    "language",
    "question",
    "answer",
    "category",
    "status",
]

COLUMN_ALIASES = {
    "ticket_id": [
        "ticket_id",
        "id",
        "case_id",
        "request_id",
        "appeal_id",
        "номер",
        "номер обращения",
        "номер тикета",
        "id обращения",
        "тикет",
        "обращение",
    ],

    "created_at": [
        "created_at",
        "created",
        "date",
        "datetime",
        "created_date",
        "дата",
        "дата создания",
        "дата обращения",
        "время создания",
    ],

    "language": [
        "language",
        "lang",
        "til",
        "язык",
    ],

    "question": [
        "question",
        "client_question",
        "user_question",
        "request",
        "message",
        "text",
        "client_message",
        "вопрос",
        "вопрос клиента",
        "сообщение клиента",
        "текст обращения",
        "запрос",
        "обращение клиента",
        "savol",
        "murojaat",
    ],

    "answer": [
        "answer",
        "operator_answer",
        "reply",
        "response",
        "solution",
        "javob",
        "ответ",
        "ответ оператора",
        "решение",
        "комментарий оператора",
    ],

    "category": [
        "category",
        "topic",
        "subject",
        "theme",
        "категория",
        "тема",
        "тип обращения",
        "раздел",
        "kategotia",
        "mavzu",
    ],

    "staus": [
        "status",
        "state",
        "result",
        "статус",
        "состояние",
        "результат",
        "holat",
    ],
}


GOOD_STATUSES = {
    "closed",
    "resolved",
    "done",
    "completed",
    "закрыт",
    "закрыто",
    "решен",
    "решён",
    "выполнен",
    "обработан",
    "hal qilindi",
    "yopilgan",
}

BAD_ANSWERS_PHRASES = [
    "не знаю",
    "уточните",
    "перезвоните",
    "обратитесь в поддержку",
    "передано специалисту",
    "проверьте позже",
    "ожидайте",
    "мы свяжемся",
    "нет информации",
    "не могу ответить",
]
