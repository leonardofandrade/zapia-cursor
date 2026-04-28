import pytest
from django.db import IntegrityError

from imports.models import Chat, Participant, ParticipantLink


@pytest.mark.django_db
def test_participant_can_have_multiple_distinct_links():
    chat = Chat.objects.create(title="Chat Teste")
    participant = Participant.objects.create(chat=chat, display_name="Alice")

    ParticipantLink.objects.create(
        participant=participant, label="Instagram", url="https://instagram.com/alice"
    )
    ParticipantLink.objects.create(
        participant=participant, label="LinkedIn", url="https://linkedin.com/in/alice"
    )

    assert ParticipantLink.objects.filter(participant=participant).count() == 2


@pytest.mark.django_db
def test_prevent_duplicate_url_for_same_participant():
    chat = Chat.objects.create(title="Chat Teste 2")
    participant = Participant.objects.create(chat=chat, display_name="Bob")
    ParticipantLink.objects.create(participant=participant, url="https://example.com/bob")

    with pytest.raises(IntegrityError):
        ParticipantLink.objects.create(participant=participant, url="https://example.com/bob")
