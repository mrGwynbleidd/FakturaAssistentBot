
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


import argparse

from app.importers.import_report import make_import_quality_report, format_import_quality_report, save_report_to_logs

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate quality report for imported call center tickets"
    )

    parser.add_argument(
        "--save",
        action="store_true",
        help="Save report to data/logs",
    )

    args = parser.parse_args()

    report = make_import_quality_report()
    text = format_import_quality_report(report)

    print(text)

    if args.save:
        path = save_report_to_logs(text)
        print("\nReport saved:")
        print(path)

if __name__ == "__main__":
    main()


