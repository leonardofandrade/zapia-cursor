from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo
from zipfile import ZipFile

from django.db import transaction
from django.utils import timezone

from imports.domain.parsing import parse_chat_text, pick_chat_txt_name
from imports.domain.types import LocalePreference
from imports.models import Chat, ImportJob, Message, Participant


@dataclass(slots=True)
class IngestSummary:
    imported_messages: int = 0
    duplicated_messages: int = 0
    participants_total: int = 0
    media_refs_found: int = 0
    missing_media_refs: int = 0

    def as_dict(self) -> dict:
        return {
            "imported_messages": self.imported_messages,
            "duplicated_messages": self.duplicated_messages,
            "participants_total": self.participants_total,
            "media_refs_found": self.media_refs_found,
            "missing_media_refs": self.missing_media_refs,
        }


def ingest_whatsapp_zip(
    zip_path: str,
    *,
    timezone_name: str = "America/Fortaleza",
    chat_name: str | None = None,
    dry_run: bool = False,
) -> IngestSummary:
    zip_file = Path(zip_path)
    if not zip_file.exists():
        raise FileNotFoundError(f"Arquivo ZIP nao encontrado: {zip_path}")

    zip_bytes = zip_file.read_bytes()
    zip_sha = hashlib.sha256(zip_bytes).hexdigest()
    tz = ZoneInfo(timezone_name)

    with ZipFile(zip_file) as archive:
        members = archive.namelist()
        chat_txt = pick_chat_txt_name(members)
        text = archive.read(chat_txt).decode("utf-8-sig", errors="replace")
        parsed = parse_chat_text(
            text,
            chat_title=chat_name or Path(chat_txt).stem,
            source_txt_name=chat_txt,
            locale_preference=LocalePreference.PT_BR,
        )

    summary = IngestSummary()
    media_member_names = {Path(m).name for m in members if not m.lower().endswith(".txt")}
    all_media_refs = [ref for msg in parsed.messages for ref in msg.media_refs]
    summary.media_refs_found = len(all_media_refs)
    summary.missing_media_refs = sum(
        1 for ref in all_media_refs if ref != "<Media omitted>" and ref not in media_member_names
    )

    if dry_run:
        summary.participants_total = len(parsed.participants)
        return summary

    with transaction.atomic():
        import_job, created = ImportJob.objects.get_or_create(
            sha256_zip=zip_sha,
            defaults={
                "arquivo_original": zip_file.name,
                "status": ImportJob.Status.RUNNING,
            },
        )
        if not created and import_job.status == ImportJob.Status.COMPLETED:
            summary.duplicated_messages = Message.objects.filter(
                chat__title=parsed.chat_title,
            ).count()
            summary.participants_total = Participant.objects.filter(chat__title=parsed.chat_title).count()
            return summary

        chat, _ = Chat.objects.get_or_create(title=parsed.chat_title)
        participants = {
            name: Participant.objects.get_or_create(chat=chat, display_name=name)[0]
            for name in sorted(parsed.participants)
        }
        summary.participants_total = len(participants)

        candidates: list[Message] = []
        for msg in parsed.messages:
            participant = participants.get(msg.sender) if msg.sender else None
            content_hash = _build_message_hash(
                timestamp=msg.timestamp.replace(tzinfo=tz).isoformat(),
                sender=msg.sender,
                text=msg.text,
                media_refs=msg.media_refs,
            )
            candidates.append(
                Message(
                    chat=chat,
                    participant=participant,
                    timestamp=msg.timestamp.replace(tzinfo=tz),
                    text=msg.text,
                    is_system=msg.is_system,
                    content_hash=content_hash,
                    raw_line=msg.raw_line,
                    media_refs=msg.media_refs,
                )
            )

        existing_keys = {
            (
                row["participant_id"],
                row["timestamp"],
                row["content_hash"],
            )
            for row in Message.objects.filter(chat=chat).values("participant_id", "timestamp", "content_hash")
        }
        to_create = []
        duplicated = 0
        for item in candidates:
            key = (item.participant_id, item.timestamp, item.content_hash)
            if key in existing_keys:
                duplicated += 1
                continue
            existing_keys.add(key)
            to_create.append(item)

        for chunk in _chunks(to_create, 500):
            Message.objects.bulk_create(chunk, ignore_conflicts=True)

        summary.imported_messages = len(to_create)
        summary.duplicated_messages = duplicated

        import_job.status = ImportJob.Status.COMPLETED
        import_job.finished_at = timezone.now()
        import_job.summary_json = json.loads(json.dumps(summary.as_dict()))
        import_job.save(update_fields=["status", "finished_at", "summary_json"])

    return summary


def _build_message_hash(*, timestamp: str, sender: str | None, text: str, media_refs: list[str]) -> str:
    normalized_text = " ".join(text.split())
    normalized_sender = (sender or "").strip().lower()
    refs = ",".join(sorted(media_refs))
    base = "|".join([timestamp, normalized_sender, normalized_text, refs])
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def _chunks(items: list[Message], size: int):
    for idx in range(0, len(items), size):
        yield items[idx : idx + size]
