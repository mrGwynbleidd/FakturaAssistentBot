# group chat handlers — collects questions and photos from monitored telegram groups
# does NOT send AI answers; it only saves data for admin review and learning pipeline
#
# how groups are registered:
#   group admin sends /readonly in the group -> bot adds it to the monitored list
#   /readonly again in the same group -> removes it (toggle)
#
# message flow:
#   user text   -> saved to group_qa.csv as "pending"
#   user photo  -> file saved to disk + logged in group_photos.csv + group_qa.csv
#   admin reply -> linked to original question, pushed to approved.csv learning pipeline
#
# IsCollectingGroup filter gates all handlers at filter level (not inside handler)
# so messages from non-monitored groups fall through to user_router

import logging
from pathlib import Path

from aiogram import Router, F
from aiogram.filters import Command, Filter
from aiogram.types import Message
from aiogram.enums import ChatType

from app.bot.photo_collector import save_group_photo
from app.logs.group_qa_logger import (
    save_group_question,
    load_pending_question,
    save_admin_answer,
)
from app.admin.services.read_only_service import (
    is_collecting_for_chat,
    add_read_only_chat,
    remove_read_only_chat,
    get_chats,
)

log = logging.getLogger("bot")

# router is restricted to group and supergroup chats only
group_router = Router()
group_router.message.filter(F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}))

# ---- admin username list -------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]
ADMINS_FILE = BASE_DIR / "data" / "group_admins_usernames.txt"


def _load_admin_usernames() -> set:
    # reads group_admins_usernames.txt, returns lowercase set without @ prefix
    if not ADMINS_FILE.exists():
        return set()
    usernames = set()
    with open(ADMINS_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            usernames.add(line.lstrip("@").lower())
    return usernames


def _is_group_admin(username):
    if not username:
        return False
    return username.lower() in _load_admin_usernames()


# ---- filter: only process messages from monitored (read-only) groups ----------
# moving the gate here (not inside handler) ensures non-monitored groups
# pass all messages through to user_router instead of silently consuming them

class IsCollectingGroup(Filter):
    async def __call__(self, message: Message) -> bool:
        return is_collecting_for_chat(message.chat.id)


# ---- helpers ------------------------------------------------------------------

def _chat_title(msg: Message) -> str:
    return msg.chat.title or str(msg.chat.id)


def _username(msg: Message) -> str:
    if msg.from_user and msg.from_user.username:
        return msg.from_user.username
    return ""


# ---- /readonly command: toggle this group in the monitored list ---------------

@group_router.message(Command("readonly"))
async def toggle_readonly(message: Message) -> None:
    # only group admins (from group_admins_usernames.txt) can toggle
    username = _username(message)
    if not _is_group_admin(username):
        return

    chat_id = message.chat.id
    title = _chat_title(message)
    chat_username = message.chat.username or ""

    current_chats = get_chats()
    already_monitored = str(chat_id) in current_chats

    if already_monitored:
        remove_read_only_chat(chat_id=chat_id, admin_id=message.from_user.id)
        await message.answer(
            "Stop Read-only for this group.\n"
            "Bot will no longer collect messages from this group."
        )
        log.info("Read-only OFF: %s (%s) by @%s", title, chat_id, username)
    else:
        add_read_only_chat(
            chat_id=chat_id,
            title=title,
            username=chat_username,
            admin_id=message.from_user.id,
        )
        await message.answer(
            "Read-only enabled for this group.\n"
            "Bot will silently collect questions from this group."
        )
        log.info("Read-only ON: %s (%s) by @%s", title, chat_id, username)


# ---- photo handler ------------------------------------------------------------

@group_router.message(F.photo, IsCollectingGroup())
async def group_photo_handler(message: Message) -> None:
    username = _username(message)

    # photos from group admins are skipped (usually illustrative, not questions)
    if _is_group_admin(username):
        return

    saved_path = await save_group_photo(message)

    caption = (message.caption or "").strip()
    question_text = caption if caption else "[photo without caption]"

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


# ---- text handler -------------------------------------------------------------
# ~F.text.startswith("/") excludes commands so they reach user_router handlers
# IsCollectingGroup() ensures only monitored groups are collected from

@group_router.message(F.text & ~F.text.startswith("/"), IsCollectingGroup())
async def group_text_handler(message: Message) -> None:
    username = _username(message)
    text = (message.text or "").strip()

    if not text:
        return

    # case a: group admin replies to a logged message -> capture as approved answer
    if _is_group_admin(username) and message.reply_to_message is not None:
        original_msg_id = message.reply_to_message.message_id
        pending = load_pending_question(message.chat.id, original_msg_id)

        if pending is not None:
            question_text = pending.get("question_text", "").strip() or (
                message.reply_to_message.text or message.reply_to_message.caption or ""
            ).strip()

            save_admin_answer(
                chat_id=message.chat.id,
                original_message_id=original_msg_id,
                admin_user_id=message.from_user.id,
                admin_username=username,
                admin_answer=text,
                question_text=question_text,
            )
            log.info("Group: @%s answered question msg_id=%s", username, original_msg_id)
        else:
            log.debug(
                "Group: @%s replied to msg_id=%s but not found in cache",
                username, original_msg_id,
            )
        return  # admin reply is not logged as a user question

    # case b: regular user message -> log as pending question
    if not _is_group_admin(username):
        save_group_question(
            chat_id=message.chat.id,
            chat_title=_chat_title(message),
            message_id=message.message_id,
            user_id=message.from_user.id,
            username=username,
            question_type="text",
            question_text=text,
        )
