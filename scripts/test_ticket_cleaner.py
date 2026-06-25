import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


from app.importers.text_cleaner import normalize_ticket_fields, get_ticket_quality_reasons

def main() -> None:
    raw_ticket = {
        "ticket_id": "12345",
        "created_at": "2026-06-24 12:30:00",
        "language": "русский",
        "question": """
            Клиент: Здравствуйте, у меня не отправляется счет фактура, тнн, тест тестирование. Почему пустой вопрос .
        """,
        "answer": """
            Оператор: Для отправки счет-фактуры откройте раздел Документы,
            выберите Счет-фактура и нажмите Отправить.
            С уважением, служба поддержки.
        """,
        "category": "счет фактура",
        "status": "решён",
    }

    normalized = normalize_ticket_fields(raw_ticket)
    reasons = get_ticket_quality_reasons(raw_ticket)

    print("NORMALIZED TICKET:")
    for key, value in normalized.items():
        print(f"{key}: {value}")

    print("\nQUALITY REASONS:")
    if reasons:
        for reason in reasons:
            print("-", reason)
    else:
        print("No problem found")

if __name__ == "__main__":
    main()

