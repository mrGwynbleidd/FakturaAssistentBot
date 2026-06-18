
import os
from typing import Any

# def normalize_admin_ids(raw_admin_ids) ->set[int]:

#     if not raw_admin_ids:
#         return set()
    
#     if isinstance(raw_admin_ids, set):
#         return {int(admin_id) for admin_id in raw_admin_ids}
    
#     if isinstance(raw_admin_ids, list):
#         return {int(admin_id) for admin_id in raw_admin_ids}
    
#     if isinstance(raw_admin_ids, tuple):
#         return {int(admin_id) for admin_id in raw_admin_ids}
    
#     if isinstance(raw_admin_ids, str):
#         result = set()

#         for item in raw_admin_ids.split(","):
#             item = item.strip()

#             if item.isdigit():
#                 result.add(int(item))

#         return result
    
#     return set()

# ADMIN_ID_SET = normalize_admin_ids(ADMIN_IDS)

#get admin ids from app.config
def get_raw_admin_ids() -> Any:

    try:
        from app.config import ADMIN_IDS

        if ADMIN_IDS:
            return ADMIN_IDS
        
    except ImportError:
        pass

    return os.getenv("ADMIN_IDS", "")


def parse_admin_ids(raw_admin_ids: Any) -> set[int]:

    if raw_admin_ids is None:
        return set()
    
    if isinstance(raw_admin_ids, int):
        return {raw_admin_ids}
    
    if isinstance(raw_admin_ids, list | tuple | set):
        result = set()

        for item in raw_admin_ids:
            try:
                result.add(int(str(item).strip()))

            except ValueError:
                continue

        return result

    raw_text = str(raw_admin_ids).strip()

    if not raw_text:
        return set()
    
    raw_text = raw_text.replace("[", "")
    raw_text = raw_text.replace("]", "")
    raw_text = raw_text.replace('"', "")
    raw_text = raw_text.replace("'", "")

    parts = raw_text.split(",")

    result = set()

    for part in parts:
        part = part.strip()

        if not part:
            continue

        try:
            result.add(int(part))
        except ValueError:
            continue

    return result



def get_admin_ids() -> set[int]:
    raw_admin_ids = get_raw_admin_ids()
    return parse_admin_ids(raw_admin_ids)

#Ckeck if user is admin

def is_admin_user(user_id: int | str | None) -> bool:

    if user_id is None:
        return False
    
    try:
        user_id_int = int(user_id)
    
    except ValueError:
        return False
    
    return user_id_int in get_admin_ids()

