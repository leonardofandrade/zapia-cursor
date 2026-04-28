from __future__ import annotations

import re
from dataclasses import replace
from datetime import datetime
from pathlib import Path

from dateutil import parser as date_parser

from .types import LocalePreference, ParsedChat, ParsedMessage

MESSAGE_RE = re.compile(
    r"^\[?(?P<date>\d{1,2}[\/\.]\d{1,2}[\/\.]\d{2,4})[,\s]+(?P<time>\d{1,2}:\d{2}(?::\d{2})?(?:\s?[APMapm\.]{2,4})?)\]?\s*[-–]\s*(?P<body>.+)$"
)
ATTACHED_RE = re.compile(r"<attached:\s*([^>]+)>", re.IGNORECASE)
MEDIA_OMITTED_RE = re.compile(r"<media omitted>", re.IGNORECASE)


def pick_chat_txt_name(members: list[str]) -> str:
    txt_members = [m for m in members if m.lower().endswith(".txt")]
    if not txt_members:
        raise ValueError("ZIP sem arquivo .txt de conversa")

    preferred = [m for m in txt_members if Path(m).name.lower() == "_chat.txt"]
    if preferred:
        return sorted(preferred)[0]

    named_whatsapp = [
        m for m in txt_members if Path(m).name.lower().startswith("whatsapp chat with")
    ]
    if named_whatsapp:
        return sorted(named_whatsapp)[0]

    return sorted(txt_members)[0]


def parse_chat_text(
    content: str,
    *,
    chat_title: str,
    source_txt_name: str,
    locale_preference: LocalePreference = LocalePreference.PT_BR,
) -> ParsedChat:
    participants: set[str] = set()
    messages: list[ParsedMessage] = []
    current: ParsedMessage | None = None

    for raw_line in content.splitlines():
        line = raw_line.strip("\ufeff")
        match = MESSAGE_RE.match(line)
        if match:
            if current is not None:
                messages.append(current)

            timestamp = _parse_timestamp(
                date_chunk=match.group("date"),
                time_chunk=match.group("time"),
                locale_preference=locale_preference,
            )
            sender, text, is_system = _extract_sender_and_text(match.group("body"))
            media_refs = _extract_media_refs(text)
            if sender:
                participants.add(sender)
            current = ParsedMessage(
                timestamp=timestamp,
                sender=sender,
                text=text,
                is_system=is_system,
                media_refs=media_refs,
                raw_line=raw_line,
            )
            continue

        if current is not None:
            appended_text = f"{current.text}\n{raw_line}".strip()
            current = replace(current, text=appended_text, media_refs=_extract_media_refs(appended_text))

    if current is not None:
        messages.append(current)

    return ParsedChat(
        chat_title=chat_title,
        participants=participants,
        messages=messages,
        source_txt_name=source_txt_name,
    )


def _parse_timestamp(
    *, date_chunk: str, time_chunk: str, locale_preference: LocalePreference
) -> datetime:
    normalized = time_chunk.replace(".", "").upper()
    dt = date_parser.parse(
        f"{date_chunk} {normalized}",
        dayfirst=locale_preference == LocalePreference.PT_BR,
        fuzzy=False,
    )
    return dt


def _extract_sender_and_text(body: str) -> tuple[str | None, str, bool]:
    if ": " in body:
        sender, text = body.split(": ", 1)
        return sender.strip(), text.strip(), False
    return None, body.strip(), True


def _extract_media_refs(text: str) -> list[str]:
    refs = [match.group(1).strip() for match in ATTACHED_RE.finditer(text)]
    if MEDIA_OMITTED_RE.search(text):
        refs.append("<Media omitted>")
    return refs
