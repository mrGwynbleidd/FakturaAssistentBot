
import csv
import sys
from collections import Counter
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


ANSWER_MODE_LOG_PATH = ROOT_DIR / "data" / "logs" / "answer_modes.csv"


def read_rows() -> list[dict]:
    if not ANSWER_MODE_LOG_PATH.exists():
        print(f"Log file not found: {ANSWER_MODE_LOG_PATH}")
        return []

    with open(
        ANSWER_MODE_LOG_PATH,
        mode="r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(file)
        return list(reader)


def main() -> None:
    rows = read_rows()

    if not rows:
        print("No answer mode logs found.")
        return

    print("Total logs:", len(rows))

    mode_counter = Counter(row.get("mode", "") for row in rows)
    source_counter = Counter(row.get("source_type", "") for row in rows)

    print("\nModes:")
    for mode, count in mode_counter.most_common():
        print(f"- {mode}: {count}")

    print("\nSources:")
    for source_type, count in source_counter.most_common():
        print(f"- {source_type}: {count}")

    print("\nLatest 10 logs:")
    for row in rows[-10:]:
        print(
            f"- mode={row.get('mode')} | "
            f"source={row.get('source_type')} | "
            f"source_id={row.get('source_id')} | "
            f"score={row.get('score')} | "
            f"question={row.get('question', '')[:120]} | "
            f"matched={row.get('matched_question', '')[:120]}"
        )


if __name__ == "__main__":
    main()
