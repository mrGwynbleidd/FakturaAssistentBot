
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


import argparse
from collections import Counter

from app.importers.backup_utils import create_learning_backup
from app.importers.call_center_reader import load_call_center_tickets, get_missing_required_fields

from app.importers.duplicate_checker import check_duplicate_in_approved, duplicate_result_to_dict
from app.importers.ticket_classifier import classify_ticket, DESTINATION_APPROVED
from app.importers.ticket_writer import ensure_learning_csv_files, write_classified_ticket


def print_column_info(headers: list[str], column_mapping: dict[str, str]) -> None:
    print("\nDetected columns:")
    for index, header in enumerate(headers, start=1):
        print(f"{index}. {header}")
    
    print("\nDetected mapping:")
    for standard_field, source_column in column_mapping.items():
        print(f"{standard_field} <- {source_column}")

    missing_required = get_missing_required_fields(column_mapping)

    if missing_required:
        print("\nWARNING: Missing required fields:")
        for field in missing_required:
            print(f"- {field}")

def process_ticket_dry_run(ticket: dict) -> dict:
    classification = classify_ticket(ticket)

    if classification.destination == DESTINATION_APPROVED:
        duplicate_result = check_duplicate_in_approved(
            ticket=classification.normalized_ticket,
        )

        if duplicate_result.is_duplicate:
            return {
                "destination": "skipped_duplicate",
                "written": False,
                "reasons": duplicate_result.reason,
                "duplicate": duplicate_result_to_dict(duplicate_result),
                "ticket_id": classification.normalized_ticket.get("ticket_id", ""),
            }
        
    return {
        "destination": classification.destination,
        "written": False,
        "reasons": ";".join(classification.reasons),
        "ticket_id": classification.normalized_ticket.get("ticket_id", ""),
    }


def process_ticket_write(ticket: dict) -> dict:
    classification = classify_ticket(ticket)

    result = write_classified_ticket(
        classification=classification,
        check_duplicates=True,
    )

    result["ticket_id"] = classification.normalized_ticket.get("ticket_id", "")
    result["reasons"] = ';'.join(classification.reasons)

    return result


def print_examples(results: list[dict], limit: int = 5) -> None:
    print("\nExamples:")
    for result in results[:limit]:
        print(
            f"- ticket_id={result.get('ticket_id')} |"
            f"destination={result.get('destination')} |"
            f"written={result.get('written')} |"
            f"reasons={result.get('reasons') or result.get('reason', '')}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import call center tickets into approved / needs_review / import_errors"
    )

    parser.add_argument(
        "file",
        help="Path to call center CSV/XLSX file. Example: data/import/call_center_tickets.xlsx",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Analyze file without writing to approved / needs_review / import_errors"
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Process only first N tickets. Useful for testing",
    )

    args = parser.parse_args()

    file_path = Path(args.file)

    print("Call center import started")
    print("File:", file_path)
    print("Dry run:", args.dry_run)

    tickets, column_mapping, headers = load_call_center_tickets(file_path)

    print_column_info(
        headers=headers,
        column_mapping=column_mapping,
    )

    if args.limit and args.limit > 0:
        tickets = tickets[:args.limit]

    print("\nTickets loaded:", len(tickets))

    missing_required = get_missing_required_fields(column_mapping)

    if missing_required:
        print("\nImport stopped because required columns are missing")
        print("Required fields:", ", ".join(missing_required))
        return
    
    if not args.dry_run:
        backup_dir = create_learning_backup()
        print("\nBackup created:", backup_dir)

        ensure_learning_csv_files()

    stats = Counter()
    results = []

    for ticket in tickets:
        if args.dry_run:
            result = process_ticket_dry_run(ticket)
        else:
            result = process_ticket_write(ticket)

        destination = result.get("destination", "unknown")

        stats[destination] +=1
        results.append(result)

    print("\nImport summary:")
    print("Total processed:", len(results))

    for destination, count in stats.most_common():
        print(f"{destination}: {count}")

    print_examples(results)

    if args.dry_run:
        print("\nDry run finished. No files were changed")
        print("Run without --dry-run to write results")
    else:
        print("\nImport finished")
        print("Updated files:")
        print("- data/learning/approved.csv")
        print("- data/learning/needs_review.csv")
        print("- data/learning/import_errors.csv")

if __name__  == "__main__":
    main()