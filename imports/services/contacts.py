from __future__ import annotations

import re
import unicodedata


def infer_contact_display_name(raw_name: str) -> str:
    name = (raw_name or "").strip()
    name = re.sub(r"\s+", " ", name)
    return name


def normalize_contact_name(raw_name: str) -> str:
    display = infer_contact_display_name(raw_name).lower()
    without_accents = "".join(
        ch for ch in unicodedata.normalize("NFKD", display) if not unicodedata.combining(ch)
    )
    normalized = re.sub(r"[^a-z0-9]+", " ", without_accents).strip()
    return re.sub(r"\s+", " ", normalized)
