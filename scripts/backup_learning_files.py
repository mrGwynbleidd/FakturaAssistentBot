
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.importers.backup_utils import create_learning_backup, list_backups


def main() -> None:
    backup_dir = create_learning_backup()

    print("Backup created:")
    print(backup_dir)

    print('\nExisting backups:')
    for backup in list_backups()[:10]:
        print("-", backup)


if __name__ == "__main__":
    main()

