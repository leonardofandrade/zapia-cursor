from datetime import datetime

import pytest
from django.urls import reverse
from django.utils import timezone

from imports.models import Chat, MediaAsset, Message, Participant


@pytest.mark.django_db
def test_media_asset_content_endpoint_returns_binary_payload(client):
    chat = Chat.objects.create(title="Grupo Midia")
    participant = Participant.objects.create(chat=chat, display_name="Alice")
    message = Message.objects.create(
        chat=chat,
        participant=participant,
        timestamp=timezone.make_aware(datetime(2026, 4, 28, 12, 0, 0)),
        text="<Media omitted>",
        content_hash="hash-1",
    )
    media = MediaAsset.objects.create(
        chat=chat,
        message=message,
        original_name="IMG-001.jpg",
        sha256="a" * 64,
        payload=b"fake-image",
        mime="image/jpeg",
        size_bytes=10,
    )

    response = client.get(reverse("imports:media_asset_content", args=[media.id]))
    assert response.status_code == 200
    assert response["Content-Type"] == "image/jpeg"
    assert response.content == b"fake-image"


@pytest.mark.django_db
def test_chat_detail_recovers_media_by_reference_name_when_fk_missing(client):
    chat = Chat.objects.create(title="Grupo Midia Ref")
    participant = Participant.objects.create(chat=chat, display_name="Alice")
    message = Message.objects.create(
        chat=chat,
        participant=participant,
        timestamp=timezone.make_aware(datetime(2026, 4, 28, 12, 5, 0)),
        text="<Media omitted>",
        content_hash="hash-2",
        media_refs=["IMG-XYZ.jpg"],
    )
    media = MediaAsset.objects.create(
        chat=chat,
        message=None,
        original_name="img-xyz.jpg",
        sha256="b" * 64,
        payload=b"fake-image-2",
        mime="image/jpeg",
        size_bytes=12,
    )

    response = client.get(reverse("imports:chat_detail", args=[chat.id]))
    assert response.status_code == 200
    assert reverse("imports:media_asset_content", args=[media.id]) in response.content.decode("utf-8")
