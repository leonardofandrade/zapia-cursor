from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class LocalePreference(str, Enum):
    PT_BR = "pt-BR"
    EN_US = "en-US"


@dataclass(slots=True)
class ParsedMessage:
    timestamp: datetime
    sender: str | None
    text: str
    is_system: bool
    media_refs: list[str] = field(default_factory=list)
    raw_line: str = ""


@dataclass(slots=True)
class ParsedChat:
    chat_title: str
    participants: set[str]
    messages: list[ParsedMessage]
    source_txt_name: str
