"""
Convert LLM-generated Markdown to Telegram-compatible Markdown (legacy mode).

Telegram legacy Markdown:
  *bold*        — жирный
  _italic_      — курсив
  `code`        — инлайн-код
  ```code```    — блок кода

LLM (Gemini) обычно генерирует:
  **bold**      — не работает в Telegram (показывается как **)
  *italic*      — Telegram воспринимает как жирный, не как курсив
  __underline__ — не работает
"""

import re


def to_telegram_md(text: str) -> str:
    """
    Конвертирует стандартный Markdown в формат Telegram (legacy Markdown).

    Шаги:
    1. **bold** / __bold__ → временный маркер §B§
    2. *italic*             → _italic_
    3. §B§                 → *  (итоговый жирный Telegram)
    """
    # 1. Защищаем **жирный** и __жирный__ временным маркером
    text = re.sub(r'\*\*(.+?)\*\*', r'§B§\1§B§', text, flags=re.DOTALL)
    text = re.sub(r'__(.+?)__',     r'§B§\1§B§', text, flags=re.DOTALL)

    # 2. Оставшиеся одиночные *текст* → _текст_ (курсив в Telegram)
    text = re.sub(r'\*([^*\n]+?)\*', r'_\1_', text)

    # 3. Возвращаем жирный маркер как Telegram-bold
    text = text.replace('§B§', '*')

    return text


def safe_markdown_answer(text: str) -> str:
    """
    Применяет to_telegram_md и возвращает готовый текст.
    Используется перед отправкой ответа бота пользователю.
    """
    return to_telegram_md(text)
