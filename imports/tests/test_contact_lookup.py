from datetime import datetime

import pytest
from django.utils import timezone

from imports.models import Chat, Message, Participant
from imports.services.contact_lookup import find_contact_chat_interactions


@pytest.mark.django_db
def test_find_contact_chat_interactions_returns_related_chats():
    chat_a = Chat.objects.create(title="Grupo A")
    chat_b = Chat.objects.create(title="Grupo B")
    alice_a = Participant.objects.create(chat=chat_a, display_name="Alice")
    alice_b = Participant.objects.create(chat=chat_b, display_name="Alice")
    bob_b = Participant.objects.create(chat=chat_b, display_name="Bob")

    ts = timezone.make_aware(datetime(2026, 4, 28, 10, 0, 0))
    Message.objects.create(chat=chat_a, participant=alice_a, timestamp=ts, content_hash="a", text="oi")
    Message.objects.create(chat=chat_a, participant=alice_a, timestamp=ts, content_hash="b", text="oi2")
    Message.objects.create(chat=chat_b, participant=alice_b, timestamp=ts, content_hash="c", text="ola")
    Message.objects.create(chat=chat_b, participant=bob_b, timestamp=ts, content_hash="d", text="opa")

    rows = find_contact_chat_interactions("ali")

    assert len(rows) == 2
    assert rows[0].chat_title == "Grupo A"
    assert rows[0].messages_count == 2
    assert rows[1].chat_title == "Grupo B"
    assert rows[1].messages_count == 1


@pytest.mark.django_db
def test_find_contact_chat_interactions_ignores_participants_without_messages():
    chat = Chat.objects.create(title="Grupo C")
    Participant.objects.create(chat=chat, display_name="Carol")

    rows = find_contact_chat_interactions("carol")
    assert rows == []
