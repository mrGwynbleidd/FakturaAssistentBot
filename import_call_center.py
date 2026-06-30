#!/usr/bin/env python3
"""
Root-level entry point for call center ticket import.
Usage:
    python import_call_center.py data/import/tickets.xlsx
    python import_call_center.py data/import/tickets.csv --dry-run
    python import_call_center.py data/import/tickets.xlsx --limit 50

Delegates to scripts/import_call_center_tickets.py
"""
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.import_call_center_tickets import main

if __name__ == "__main__":
    main()
