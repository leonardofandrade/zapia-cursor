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
