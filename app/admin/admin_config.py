#parses and provides the set of admin telegram user ids from config or environment
#used by admin_access.is_admin to check if a user has admin privileges

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

#reads raw ADMIN_IDS value from app.config, falls back to os.getenv if import fails
#used in get_admin_ids
def get_raw_admin_ids() -> Any:

    try:
        from app.config import ADMIN_IDS

        if ADMIN_IDS:
            return ADMIN_IDS
        
    except ImportError:
        pass

    return os.getenv("ADMIN_IDS", "")


#converts raw admin ids in any format (str, list, int, set) to a set of ints
#handles comma-separated strings, bracket notation, and quoted values
#used in get_admin_ids
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
    
    #strip list formatting characters
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


#returns the current set of admin user ids as ints
#used in is_admin_user
def get_admin_ids() -> set[int]:
    raw_admin_ids = get_raw_admin_ids()
    return parse_admin_ids(raw_admin_ids)

#returns true if the given user_id is in the admin ids set
#used throughout admin handlers to guard admin-only actions
def is_admin_user(user_id: int | str | None) -> bool:

    if user_id is None:
        return False
    
    try:
        user_id_int = int(user_id)
    
    except ValueError:
        return False
    
    return user_id_int in get_admin_ids()
