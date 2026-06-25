
#import libs
import json
import shutil
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]

LEARNING_DIR = BASE_DIR / "data" / "learning"
BACKUPS_DIR = BASE_DIR / "data" / "backups"

LEARNING_FILES = [
    "approved.csv",
    "needs_review.csv",
    "import_errors.csv",
]

def get_timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

def ensure_backup_dirs() -> None:
    LEARNING_DIR.mkdir(parents=True, exist_ok=True)
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)

def create_learning_backup() -> Path:

    ensure_backup_dirs()
    
    backup_dir = BACKUPS_DIR / f"learning_backup_{get_timestamp()}"
    backup_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source_dir": str(LEARNING_DIR),
        "backup_dir": str(backup_dir),
        "copied": [],
        "skipped": [],
    }

    for filename in LEARNING_FILES:
        source_path= LEARNING_DIR / filename
        target_path = backup_dir / filename

        if source_path.exists():
            shutil.copy2(source_path, target_path)

            manifest["copied"].append(
                {
                    "filename": filename,
                    "source": str(source_path),
                    "target": str(target_path),
                    "size_bytes": source_path.stat().st_size,
                }
            )

        else:
            manifest["skipped"].append(
                {
                    "filename": filename,
                    "reason": "file_not_found",
                    "source": str(source_path),
                }
            )
    manifest_path = backup_dir / "manifest.json"

    with open(manifest_path, mode="w", encoding="utf-8-sig") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    return backup_dir


def list_backups() -> list[Path]:
    ensure_backup_dirs()

    return sorted(
        [
            path 
            for path in BACKUPS_DIR.iterdir()
            if path.is_dir() and path.name.startswith("learning_backup_")
        ],
        reverse=True,
    )

def get_latest_backup() -> Path | None:
    backups = list_backups()

    if not backups:
        return None
    
    return backups[0]
