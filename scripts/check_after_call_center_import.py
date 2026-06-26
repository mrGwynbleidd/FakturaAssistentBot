
import csv
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

APPROVED_CSV_PATH = BASE_DIR / "data" / "learning" / "approved.csv"

def read_latest_questions(limit: int = 10) -> list[str]:
    if not APPROVED_CSV_PATH.exists():
        print(f"approved.csv not found: {APPROVED_CSV_PATH}")
        return []
    
    with open(APPROVED_CSV_PATH, mode = "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    questions = []

    for row in rows[-limit:]:
        question = row.get("question", "").strip()

        if question:
            questions.append(question)
        
    return questions

def run_command(command: list[str]) -> int:
    print("\n" + "-"*80)
    print("RUN:", " ".join(command))
    print("-"*80)

    result = subprocess.run(command)

    return result.returncode


def main() -> None:
    questions = read_latest_questions(limit=10)

    if not questions:
        print("No questions found in approved.csv")
        return
    
    print("Latest approved questions:")
    for index, question in enumerate(questions, start=1):
        print(f"{index}. {question}")

    print("\nChecking latest approved questions with debug_approved_matcher.py")

    for question in questions:
        command = [
            sys.executable,
            "debug_approved_matcher.py",
            question,
        ]


        exit_code = run_command(command)

        if exit_code != 0:
            print(f"Command failed for question: {question}")


if __name__ == "__main__":
    main()
