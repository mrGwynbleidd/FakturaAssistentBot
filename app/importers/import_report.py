
import csv
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parents[2]

LEARNING_DIR = BASE_DIR / "data" / "learning"
LOGS_DIR = BASE_DIR / "data" / "logs"

APPROVED_CSV_PATH = LEARNING_DIR / "approved.csv"
NEEDS_REVIEW_CSV_PATH = LEARNING_DIR / "needs_review.csv"
IMPORT_ERRORS_CSV_PATH = LEARNING_DIR / "import_errors.csv"


def read_csv_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    
    with open(path, mode="r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)
    

def clean_text(value: Any) -> str:
    if value is None:
        return ""
    
    return " ".join(str(value).replace("\x00", " ").split())


def count_empty_values(rows: list[dict[str, Any]], column: str) -> int:
    count = 0

    for row in rows:
        if not clean_text(row.get(column, "")):
            count +=1

    return count


def count_duplicate_values(rows: list[dict[str, Any]], column: str):
    values = []

    for row in rows:
        value = clean_text(row.get(column, ""))

        if value:
            values.append(value)
        
    
    counter = Counter(values)

    return {
        value: count 
        for value, count in counter.items()
        if count >1
    }

def count_column_values(rows: list[dict[str, Any]], column: str) -> Counter:
    counter = Counter()

    for row in rows:
        value = clean_text(row.get(column, ""))

        if not value:
            value = "empty"
        
        counter[value] +=1
    
    return counter


def count_reason_values(rows: list[dict[str, Any]], column: str = "reasons") -> Counter:
    counter = Counter()

    for row in rows:
        raw_reasons = clean_text(row.get(column, ""))

        if not raw_reasons:
            counter["empty"] +=1
            continue

        for reason in raw_reasons.split(";"):
            reason = clean_text(reason)

            if reason:
                counter[reason] +=1

    return counter


def get_latest_rows(
        rows: list[dict[str, Any]],
        limit: int = 5,
)-> list[dict[str, Any]]:
    
    if not rows:
        return []
    
    return rows[-limit:]


def make_import_quality_report() -> dict[str, Any]:
    approved_rows = read_csv_rows(APPROVED_CSV_PATH)
    needs_review_rows = read_csv_rows(NEEDS_REVIEW_CSV_PATH)
    import_error_rows = read_csv_rows(IMPORT_ERRORS_CSV_PATH)

    approved_duplicate_source_ids = count_duplicate_values(approved_rows, "source_id",)

    approved_duplicate_questions = count_duplicate_values(approved_rows, "question",)

    report = {
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "files": {
            "approved": str(APPROVED_CSV_PATH),
            "needs_review": str(NEEDS_REVIEW_CSV_PATH),
            "import_errors": str(IMPORT_ERRORS_CSV_PATH),
        },
        "counts": {
            "approved": len(approved_rows),
            "needs_review": len(needs_review_rows),
            "import_errors": len(import_error_rows),
            "total": len(approved_rows) + len(needs_review_rows) + len(import_error_rows),
        },
        "quality_checks": {
            "approved_empty_question": count_empty_values(approved_rows, "question"),
            "approved_empty_answer": count_empty_values(approved_rows, "approved_answer"),
            "approved_duplicate_source_id_count": len(approved_duplicate_source_ids),
            "approved_duplicate_question_count": len(approved_duplicate_questions),
            "needs_review_empty_question": count_empty_values(needs_review_rows, "question"),
            "needs_review_empty_answer": count_empty_values(needs_review_rows, "suggested_answer"),
            "import_errors_empty_reason": count_empty_values(import_error_rows, "reason"),
        },
        "approved_categories": count_column_values(
            approved_rows,
            "category",
        ).most_common(20),
        "needs_review_reasons": count_reason_values(
            needs_review_rows,
            "reasons",
        ).most_common(20),
        "import_error_reasons": count_reason_values(
            import_error_rows,
            "reason",
        ).most_common(20),
        "duplicates": {
            "approved_source_ids": approved_duplicate_source_ids,
            "approved_questions": approved_duplicate_questions,
        },
        "latest_examples": {
            "approved": get_latest_rows(approved_rows, limit=5),
            "needs_review": get_latest_rows(needs_review_rows, limit=5),
            "import_errors": get_latest_rows(import_error_rows, limit=5),
        },
    }

    return report


def format_counter_items(items: list[tuple[str, int]]) -> list[str]:
    if not items:
        return ["- no data"]
    
    lines = []

    for value, count in items:
        lines.append(f"- {value}: {count}")

    return lines

def format_latest_examples(rows: list[dict[str, Any]], answer_column: str) -> list[str]:

    if not rows:
        return ["- no data"]
    lines = []

    for row in rows:
        source_id = clean_text(row.get("source_id", row.get("ticket_id", "")))
        question = clean_text(row.get("question", ""))[:120]
        answer = clean_text(row.get(answer_column, row.get("answer", "")))[:160]
        reason = clean_text(row.get("reasons", row.get("reason", "")))[:120]

        line = f"- source_id={source_id} | question={question}"

        if answer:
            line +=f" | answer={answer}"
        
        if reason:
            line +=f" | reason={reason}"

        lines.append(line)

    return lines

def format_import_quality_report(report: dict[str, Any]) -> str:
    lines = []

    lines.append("CALL CENTER IMPORT QUALITY REPORT")
    lines.append("=" * 80)
    lines.append(f"Created at: {report['created_at']}")
    lines.append("")

    lines.append("FILES")
    lines.append("-" * 80)
    for name, path in report["files"].items():
        lines.append(f"{name}: {path}")

    lines.append("")
    lines.append("COUNTS")
    lines.append("-" * 80)
    for name, count in report["counts"].items():
        lines.append(f"{name}: {count}")

    lines.append("")
    lines.append("QUALITY CHECKS")
    lines.append("-" * 80)
    for name, count in report["quality_checks"].items():
        status = "OK" if count == 0 else "CHECK"
        lines.append(f"{name}: {count} [{status}]")

    lines.append("")
    lines.append("APPROVED CATEGORIES")
    lines.append("-" * 80)
    lines.extend(format_counter_items(report["approved_categories"]))

    lines.append("")
    lines.append("NEEDS REVIEW REASONS")
    lines.append("-" * 80)
    lines.extend(format_counter_items(report["needs_review_reasons"]))

    lines.append("")
    lines.append("IMPORT ERROR REASONS")
    lines.append("-" * 80)
    lines.extend(format_counter_items(report["import_error_reasons"]))

    lines.append("")
    lines.append("DUPLICATES")
    lines.append("-" * 80)
    lines.append(
        f"approved source_id duplicates: "
        f"{len(report['duplicates']['approved_source_ids'])}"
    )
    lines.append(
        f"approved question duplicates: "
        f"{len(report['duplicates']['approved_questions'])}"
    )

    lines.append("")
    lines.append("LATEST APPROVED EXAMPLES")
    lines.append("-" * 80)
    lines.extend(
        format_latest_examples(
            report["latest_examples"]["approved"],
            answer_column="approved_answer",
        )
    )

    lines.append("")
    lines.append("LATEST NEEDS REVIEW EXAMPLES")
    lines.append("-" * 80)
    lines.extend(
        format_latest_examples(
            report["latest_examples"]["needs_review"],
            answer_column="suggested_answer",
        )
    )

    lines.append("")
    lines.append("LATEST IMPORT ERROR EXAMPLES")
    lines.append("-" * 80)
    lines.extend(
        format_latest_examples(
            report["latest_examples"]["import_errors"],
            answer_column="answer",
        )
    )

    return "\n".join(lines)


def save_report_to_logs(text: str) -> Path:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    filename = f"call_center_import_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    path = LOGS_DIR / filename

    with open(path, mode="w", encoding="utf-8") as f:
        f.write(text)

    return path