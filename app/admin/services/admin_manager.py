#manages data/admins.txt — add, remove, and list dynamically managed admin ids
#env-var admins (from admin_config.py) are always active and cannot be removed here
#used by settings handlers

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]
ADMINS_FILE = BASE_DIR / "data" / "admins.txt"


def _ensure_file() -> None:
    ADMINS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not ADMINS_FILE.exists():
        ADMINS_FILE.write_text("", encoding="utf-8")


def list_admins_from_file() -> list[int]:
    """Returns list of admin ids stored in data/admins.txt."""
    _ensure_file()
    result = []
    for line in ADMINS_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.isdigit():
            result.append(int(line))
    return result


def add_admin(user_id: int) -> bool:
    """Adds user_id to data/admins.txt. Returns False if already exists."""
    _ensure_file()
    existing = list_admins_from_file()
    if user_id in existing:
        return False
    with open(ADMINS_FILE, "a", encoding="utf-8") as f:
        f.write(f"{user_id}\n")
    return True


def remove_admin(user_id: int) -> bool:
    """Removes user_id from data/admins.txt. Returns False if not found."""
    _ensure_file()
    existing = list_admins_from_file()
    if user_id not in existing:
        return False
    updated = [uid for uid in existing if uid != user_id]
    ADMINS_FILE.write_text("\n".join(str(uid) for uid in updated) + ("\n" if updated else ""), encoding="utf-8")
    return True
