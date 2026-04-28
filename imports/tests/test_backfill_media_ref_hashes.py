from datetime import datetime

import pytest
from django.core.management import call_command
from django.utils import timezone

from imports.models import Chat, MediaAsset, Message, Participant


@pytest.mark.django_db
def test_backfill_media_ref_hashes_populates_map_from_filename_match():
    chat = Chat.objects.create(title="Chat Backfill")
    participant = Participant.objects.create(chat=chat, display_name="Alice")
    message = Message.objects.create(
        chat=chat,
        participant=participant,
        timestamp=timezone.make_aware(datetime(2026, 4, 28, 16, 0, 0)),
        text="<Media omitted>",
        content_hash="hash-backfill",
        media_refs=["IMG-1001.jpg"],
        media_ref_sha256_map={},
    )
    media = MediaAsset.objects.create(
        chat=chat,
        message=None,
        original_name="img-1001.jpg",
        sha256="d" * 64,
        payload=b"payload",
        mime="image/jpeg",
        size_bytes=7,
    )

    call_command("backfill_media_ref_hashes")
    message.refresh_from_db()

    assert message.media_ref_sha256_map == {"img-1001.jpg": media.sha256}
