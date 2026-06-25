import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))



from app.importers.ticket_classifier import classify_ticket, classification_to_dict

def print_result(title: str, ticket: dict) -> None:
    classification = classify_ticket(ticket)

    result = classification_to_dict(classification)

    print(title)

    for key, value in result.items():
        print(f"{key}: {value}")


def main() -> None:

    good_ticket = {
        "ticket_id": "1001",
        "created_at": "2026-06-24 12:30:00",
        "language": "русский",
        "question": "Как отправить счет-фактуру контрагенту?",
        "answer": "Для отправки счет-фактуры откройте раздел Документы, выберите нужный документ и нажмите кнопку Отправить.",
        "category": "счет фактура",
        "status": "решён",
    }

    empty_answer_ticket = {
        "ticket_id": "1002",
        "created_at": "2026-06-24 12:35:00",
        "language": "русский",
        "question": "Почему не открывается акт сверки?",
        "answer": "",
        "category": "акт сверки",
        "status":"решён",
    }

    review_ticket = {
        "ticket_id": "1003",
        "created_at": "2026-06-24 12:40:00",
        "language": "русский",
        "question": "Почему документ не отправляется?",
        "answer": "Обратитесь в поддержку.",
        "category": "документ",
        "status": "решён",
    }

    not_closed_ticket = {
        
        "ticket_id": "1004",
        "created_at": "2026-06-24 12:45:00",
        "language": "русский",
        "question": "Как выбрать оператора ЭДО?",
        "answer": "Для выбора оператора ЭДО откройте настройки организации и выберите нужного оператора из доступного списка",
        "category": "эдо",
        "status":"в работе",
    }

    print_result("GOOD_TICKET -> APPROVED", good_ticket)
    print_result("\nEMPTY ANSWER -> import_errors", empty_answer_ticket)
    print_result("\nBAD PHRASE -> needs_review", review_ticket)
    print_result("\nNOT CLOSED STATUS -> needs_review", not_closed_ticket)


if __name__ == "__main__":
    main()