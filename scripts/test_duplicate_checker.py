
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


import csv
import tempfile

from app.importers.duplicate_checker import check_duplicate_in_approved, duplicate_result_to_dict


def create_test_approved_csv() -> Path:
    temp_dir = Path(tempfile.gettempdir())
    test_file = temp_dir / "test_approved_duplicates.csv"

    rows = [
        {
            
            "case_id": "call_1001",
            "datetime": "2026-06-24 12:30:00",
            "language": "ru",
            "question": "Как отправить счет-фактуру контрагенту?",
            "approved_answer": "Для отправки счет-фактуры откройте раздел Документы, выберите нужный документ и нажмите кнопку Отправить.",
            "category": "invoice",
            "source_type": "call_center",
            "source_id": "1001",
            "status": "approved",
            "notes": "test row",
        }
    ]

    fieldnames = [
        "case_id",
        "datetime",
        "language",
        "question",
        "approved_answer",
        "category",
        "source_type",
        "source_id",
        "status",
        "notes",
    ]

    with open(test_file, mode="w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return test_file



def print_result(title: str, ticket: dict, approved_csv_path: Path):
    result = check_duplicate_in_approved(ticket=ticket, approved_csv_path=approved_csv_path)
    print("\n", title)
    
    for key, value in duplicate_result_to_dict(result).items():
        print(f"{key}: {value}")


def main() -> None:
    approved_csv_path = create_test_approved_csv()

    same_ticket_id = {
        "ticket_id": "1001",
        "question": "Как отправить счет-фактуру контрагенту?",
        "answer": "Для отправки счет-фактуры откройте раздел Документы, выберите нужный документ и нажмите кнопку Отправить.",
    }

    similar_question = {
        "ticket_id": "2002",
        "question": "Как можно отправить счет фактуру контрагенту?",
        "answer": "Для отправки счет-фактуры откройте раздел Документы, выберите нужный документ и нажмите кнопку Отправить.",
    }

    new_ticket = {
        "ticket_id": "3003",
        "question": "Как выбрать оператора ЭДО?",
        "answer": "Для выбора оператора ЭДО откройте настройки организации и выберите нужного оператора из списка.",
    }

    print_result("SAME TICKET ID -> duplicated", same_ticket_id, approved_csv_path)
    print_result("SIMILAR QUESTION -> duplicate", similar_question, approved_csv_path)
    print_result("NEW TICKET -> not duplicate", new_ticket, approved_csv_path)


if __name__ == "__main__":
    main()
