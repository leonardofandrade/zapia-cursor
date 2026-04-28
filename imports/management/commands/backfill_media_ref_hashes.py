from __future__ import annotations

from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from imports.models import MediaAsset, Message


class Command(BaseCommand):
    help = "Preenche media_ref_sha256_map em mensagens antigas usando referencias por nome de arquivo."

    def add_arguments(self, parser):
        parser.add_argument(
            "--chat-id",
            type=int,
            default=None,
            help="Opcional: processa apenas um chat especifico.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help="Opcional: limita quantidade de mensagens processadas (0 = sem limite).",
        )

    def handle(self, *args, **options):
        chat_id = options["chat_id"]
        limit = options["limit"]

        messages_qs = Message.objects.exclude(media_refs=[]).order_by("id")
        if chat_id is not None:
            messages_qs = messages_qs.filter(chat_id=chat_id)
        if limit and limit > 0:
            messages_qs = messages_qs[:limit]

        messages = list(messages_qs)
        if not messages:
            self.stdout.write(self.style.WARNING("Nenhuma mensagem elegivel para backfill."))
            return

        processed = 0
        updated = 0
        recovered_refs = 0
        unresolved_refs = 0
        lookup_cache: dict[int, dict[str, list[MediaAsset]]] = {}

        with transaction.atomic():
            for message in messages:
                processed += 1
                media_map = dict(message.media_ref_sha256_map or {})
                changed = False
                candidates_by_name = lookup_cache.setdefault(
                    message.chat_id,
                    _build_media_lookup_for_chat(message.chat_id),
                )

                for ref in message.media_refs:
                    normalized_ref = _normalize_media_ref_name(ref)
                    if not normalized_ref:
                        continue
                    if normalized_ref in media_map:
                        continue

                    candidates = candidates_by_name.get(normalized_ref, [])
                    if len(candidates) == 1:
                        media_map[normalized_ref] = candidates[0].sha256
                        recovered_refs += 1
                        changed = True
                    else:
                        unresolved_refs += 1

                if changed:
                    message.media_ref_sha256_map = media_map
                    message.save(update_fields=["media_ref_sha256_map"])
                    updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                "Backfill concluido: "
                f"mensagens processadas={processed}, "
                f"mensagens atualizadas={updated}, "
                f"refs recuperadas={recovered_refs}, "
                f"refs nao resolvidas={unresolved_refs}"
            )
        )


def _build_media_lookup_for_chat(chat_id: int) -> dict[str, list[MediaAsset]]:
    lookup: dict[str, list[MediaAsset]] = {}
    for media in MediaAsset.objects.filter(chat_id=chat_id):
        key = _normalize_media_ref_name(media.original_name)
        lookup.setdefault(key, []).append(media)
    return lookup


def _normalize_media_ref_name(value: str) -> str:
    if not value or value == "<Media omitted>":
        return ""
    return Path(value.strip().strip('"').strip("'")).name.casefold()
