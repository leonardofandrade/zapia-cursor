import zipfile
from pathlib import Path

import pytest

from imports.models import Chat, Contact, ImportJob, MediaAsset, Message, Participant
from imports.services.ingest_zip import ingest_whatsapp_zip


@pytest.fixture
def sample_zip(tmp_path: Path) -> Path:
    zip_path = tmp_path / "chat-export.zip"
    chat_text = """28/04/26, 14:30 - Alice: Oi
linha extra da mesma mensagem
28/04/26, 14:31 - Bob: <attached: IMG-0001.jpg>
"""
    media_bytes = b"fake-jpg-content"
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr("_chat.txt", chat_text)
        archive.writestr("IMG-0001.jpg", media_bytes)
    return zip_path


@pytest.mark.django_db
def test_ingest_creates_records_and_is_idempotent(sample_zip: Path, tmp_path: Path):
    first = ingest_whatsapp_zip(str(sample_zip))
    second = ingest_whatsapp_zip(str(sample_zip))

    assert first.imported_messages == 2
    assert second.imported_messages == 0
    assert Message.objects.count() == 2
    assert Participant.objects.count() == 2
    assert Chat.objects.count() == 1
    assert ImportJob.objects.count() == 1
    assert MediaAsset.objects.count() == 1


@pytest.mark.django_db
def test_media_sha_dedup_across_two_import_jobs(tmp_path: Path):
    media_bytes = b"shared-content"

    first_zip = tmp_path / "chat-a.zip"
    second_zip = tmp_path / "chat-b.zip"

    with zipfile.ZipFile(first_zip, "w") as zf:
        zf.writestr("_chat.txt", "28/04/26, 14:31 - Bob: <attached: IMG-0001.jpg>\n")
        zf.writestr("IMG-0001.jpg", media_bytes)

    with zipfile.ZipFile(second_zip, "w") as zf:
        zf.writestr("_chat.txt", "28/04/26, 15:31 - Bob: <attached: IMG-0001.jpg>\n")
        zf.writestr("IMG-0001.jpg", media_bytes)

    ingest_whatsapp_zip(str(first_zip), chat_name="Chat A")
    ingest_whatsapp_zip(str(second_zip), chat_name="Chat B")

    assert ImportJob.objects.count() == 2
    assert MediaAsset.objects.count() == 1


@pytest.mark.django_db
def test_media_payload_is_stored_in_database(sample_zip: Path):
    ingest_whatsapp_zip(str(sample_zip))

    media = MediaAsset.objects.get()
    message = Message.objects.get(participant__display_name="Bob")
    assert bytes(media.payload) == b"fake-jpg-content"
    assert message.media_ref_sha256_map == {"img-0001.jpg": media.sha256}


@pytest.mark.django_db
def test_participants_are_linked_to_global_contacts_across_chats(tmp_path: Path):
    first_zip = tmp_path / "chat-a.zip"
    second_zip = tmp_path / "chat-b.zip"

    with zipfile.ZipFile(first_zip, "w") as zf:
        zf.writestr("_chat.txt", "28/04/26, 14:31 - Jose Silva: oi\n")

    with zipfile.ZipFile(second_zip, "w") as zf:
        zf.writestr("_chat.txt", "28/04/26, 15:31 - José  Silva: ola\n")

    ingest_whatsapp_zip(str(first_zip), chat_name="Chat A")
    ingest_whatsapp_zip(str(second_zip), chat_name="Chat B")

    assert Participant.objects.count() == 2
    assert Contact.objects.count() == 1
    assert Participant.objects.exclude(contact=None).count() == 2
