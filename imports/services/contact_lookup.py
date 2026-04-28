from __future__ import annotations

from dataclasses import dataclass

from django.db.models import Count, Q

from imports.models import Participant


@dataclass(slots=True)
class ContactChatInteraction:
    chat_title: str
    participant_name: str
    messages_count: int


def find_contact_chat_interactions(contact_query: str) -> list[ContactChatInteraction]:
    query = (contact_query or "").strip()
    if not query:
        return []

    participants = (
        Participant.objects.filter(
            Q(display_name__icontains=query) | Q(contact__display_name__icontains=query)
        )
        .annotate(messages_count=Count("messages"))
        .filter(Q(messages_count__gt=0))
        .select_related("chat", "contact")
        .order_by("-messages_count", "chat__title")
    )
    return [
        ContactChatInteraction(
            chat_title=item.chat.title,
            participant_name=item.contact.display_name if item.contact_id else item.display_name,
            messages_count=item.messages_count,
        )
        for item in participants
    ]
