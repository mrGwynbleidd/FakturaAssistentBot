

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


from app.importers.ticket_classifier import classify_ticket
from app.importers.ticket_writer import (
    ensure_learning_csv_files,
    write_classified_ticket,
)


def print_result(title: str, ticket: dict) -> None:
    classification = classify_ticket(ticket)
    result = write_classified_ticket(classification)

    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)

    print("classification:", classification.destination)
    print("reasons:", classification.reasons)
    print("write result:", result)


def main() -> None:
    ensure_learning_csv_files()

    good_ticket = {
        "ticket_id": "writer_test_1001",
        "created_at": "2026-06-24 12:30:00",
        "language": "русский",
        "question": "Как отправить счет-фактуру через систему?",
        "answer": "Для отправки счет-фактуры откройте раздел Документы, выберите нужную счет-фактуру и нажмите кнопку Отправить.",
        "category": "счет фактура",
        "status": "решён",
    }

    review_ticket = {
        "ticket_id": "writer_test_1002",
        "created_at": "2026-06-24 12:35:00",
        "language": "русский",
        "question": "Почему документ не отправляется?",
        "answer": "Обратитесь в поддержку.",
        "category": "документ",
        "status": "решён",
    }

    error_ticket = {
        "ticket_id": "writer_test_1003",
        "created_at": "2026-06-24 12:40:00",
        "language": "русский",
        "question": "ок",
        "answer": "",
        "category": "документ",
        "status": "решён",
    }

    duplicate_ticket = {
        "ticket_id": "writer_test_1001",
        "created_at": "2026-06-24 12:45:00",
        "language": "русский",
        "question": "Как отправить счет-фактуру через систему?",
        "answer": "Для отправки счет-фактуры откройте раздел Документы, выберите нужную счет-фактуру и нажмите кнопку Отправить.",
        "category": "счет фактура",
        "status": "решён",
    }

    print_result("GOOD TICKET → approved.csv", good_ticket)
    print_result("REVIEW TICKET → needs_review.csv", review_ticket)
    print_result("ERROR TICKET → import_errors.csv", error_ticket)
    print_result("DUPLICATE TICKET → import_errors.csv / skipped_duplicate", duplicate_ticket)


if __name__ == "__main__":
    main()

