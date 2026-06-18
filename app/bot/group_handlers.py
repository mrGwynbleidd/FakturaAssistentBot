"""
Group chat handlers — runs only in group / supergroup chats.

What this does:
  1. User sends a photo (with optional caption) → saves file + logs question in group_qa.csv
  2. User sends text → logs question in group_qa.csv
  3. Admin replies to a logged message → links answer to original question
     and pushes it into the approved-answers learning pipeline

How admins are identified:
  - data/group_admins_usernames.txt  ← list of Telegram usernames (one per line)
  - Messages from users NOT in that list are treated as regular user messages
"""

import logging
from pathlib import Path

from aiogram import Router, F
from aiogram.types import Message
from aiogram.enums import ChatType

from app.bot.photo_collector import save_group_photo
from app.logs.group_qa_logger import (
    save_group_question,
    load_pending_question,
    save_admin_answer,
)

log = logging.getLogger("bot")

# ── router filtered to group chats only ───────────────────────────────────────
group_router = Router()
group_router.message.filter(F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}))

# ── load admin usernames ───────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parents[2]
ADMINS_FILE = BASE_DIR / "data" / "group_admins_usernames.txt"


def _load_admin_usernames() -> set[str]:
    """Read data/group_admins_usernames.txt → set of lowercase usernames (no @)."""
    if not ADMINS_FILE.exists():
        return set()
    usernames: set[str] = set()
    with open(ADMINS_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            usernames.add(line.lstrip("@").lower())
    return usernames


def _is_admin(username: str | None) -> bool:
    if not username:
        return False
    admins = _load_admin_usernames()
    return username.lower() in admins


# ── helpers ────────────────────────────────────────────────────────────────────

def _chat_title(msg: Message) -> str:
    return msg.chat.title or str(msg.chat.id)


def _username(msg: Message) -> str:
    return msg.from_user.username or ""


def _full_name(msg: Message) -> str:
    u = msg.from_user
    return (f"{u.first_name or ''} {u.last_name or ''}").strip()


# ── photo handler ──────────────────────────────────────────────────────────────

@group_router.message(F.photo)
async def group_photo_handler(message: Message) -> None:
    """Save photo file and log as a pending group question."""
    username = _username(message)

    # Photos from admins are skipped (they're usually illustrative, not questions)
    if _is_admin(username):
        return

    # Save the actual file (existing logic)
    saved_path = await save_group_photo(message)

    caption = (message.caption or "").strip()
    question_text = caption if caption else "[фото без подписи]"

    save_group_question(
        chat_id=message.chat.id,
        chat_title=_chat_title(message),
        message_id=message.message_id,
        user_id=message.from_user.id,
        username=username,
        question_type="photo",
        question_text=question_text,
        saved_photo_path=saved_path or "",
    )


# ── text message handler ───────────────────────────────────────────────────────

@group_router.message(F.text)
async def group_text_handler(message: Message) -> None:
    """
    Two cases:
    a) Admin replies to a logged user message  → capture as approved answer
    b) Regular user text (or non-reply admin)  → log as pending question
    """
    username = _username(message)
    text = (message.text or "").strip()

    if not text:
        return

    # ── Case (a): admin reply ─────────────────────────────────────────────────
    if _is_admin(username) and message.reply_to_message is not None:
        original = message.reply_to_message
        original_msg_id = original.message_id

        pending = load_pending_question(message.chat.id, original_msg_id)

        if pending is not None:
            question_text = pending.get("question_text", "").strip() or (
                original.text or original.caption or ""
            ).strip()

            save_admin_answer(
                chat_id=message.chat.id,
                original_message_id=original_msg_id,
                admin_user_id=message.from_user.id,
                admin_username=username,
                admin_answer=text,
                question_text=question_text,
            )
            log.info(
                f"✅ Группа: @{username} ответил на вопрос msg_id={original_msg_id}"
            )
        else:
            log.debug(
                f"Группа: @{username} ответил на сообщение {original_msg_id}, "
                "но вопрос не найден в кэше — пропускаем"
            )
        return  # don't log the admin reply as a question

    # ── Case (b): regular user text (or admin non-reply) ─────────────────────
    if not _is_admin(username):
        save_group_question(
            chat_id=message.chat.id,
            chat_title=_chat_title(message),
            message_id=message.message_id,
            user_id=message.from_user.id,
            username=username,
            question_type="text",
            question_text=text,
        )
