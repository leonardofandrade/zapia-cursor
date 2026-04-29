from imports.domain.parsing import parse_chat_text
from imports.domain.types import LocalePreference


def test_parse_chat_text_multiline_system_and_media():
    content = """28/04/26, 14:30 - Alice: Oi
continua aqui
28/04/26, 14:31 - Bob: <attached: IMG-0001.jpg>
28/04/26, 14:32 - Messages and calls are end-to-end encrypted.
"""
    parsed = parse_chat_text(
        content,
        chat_title="Teste",
        source_txt_name="_chat.txt",
        locale_preference=LocalePreference.PT_BR,
    )

    assert parsed.chat_title == "Teste"
    assert parsed.participants == {"Alice", "Bob"}
    assert len(parsed.messages) == 3
    assert parsed.messages[0].text == "Oi\ncontinua aqui"
    assert parsed.messages[1].media_refs == ["IMG-0001.jpg"]
    assert parsed.messages[2].is_system is True


def test_parse_chat_text_supports_pt_br_media_markers():
    content = """28/04/26, 14:31 - Bob: <anexo: IMG-0002.jpg>
28/04/26, 14:32 - Bob: <Mídia oculta>
"""
    parsed = parse_chat_text(
        content,
        chat_title="Teste PT",
        source_txt_name="_chat.txt",
        locale_preference=LocalePreference.PT_BR,
    )

    assert len(parsed.messages) == 2
    assert parsed.messages[0].media_refs == ["IMG-0002.jpg"]
    assert parsed.messages[1].media_refs == ["<Media omitted>"]


def test_parse_chat_text_supports_attached_filename_suffix_format():
    content = """28/04/26, 14:31 - Bob: IMG-20260428-WA0001.jpg (arquivo anexado)
28/04/26, 14:32 - Bob: VID-20260428-WA0002.mp4 (file attached)
"""
    parsed = parse_chat_text(
        content,
        chat_title="Teste Suffix",
        source_txt_name="_chat.txt",
        locale_preference=LocalePreference.PT_BR,
    )

    assert len(parsed.messages) == 2
    assert parsed.messages[0].media_refs == ["IMG-20260428-WA0001.jpg"]
    assert parsed.messages[1].media_refs == ["VID-20260428-WA0002.mp4"]
