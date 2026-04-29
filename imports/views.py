from django.db.models import Count
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
import re
from django.views.decorators.http import require_POST

from imports.models import Chat, Contact, MediaAsset, Message, Participant
from imports.services.contacts import infer_contact_display_name, normalize_contact_name
from imports.services.contact_lookup import find_contact_chat_interactions


def _is_media_omitted_marker(value: str) -> bool:
    normalized = (value or "").strip().casefold()
    return normalized in {
        "<media omitted>",
        "<midia oculta>",
        "<mídia oculta>",
        "<media oculta>",
        "<midia omitida>",
        "<mídia omitida>",
    }


def _clean_message_text_for_display(value: str) -> str:
    text = (value or "").strip()
    if not text:
        return ""
    # Remove marker tokens in PT/EN while preserving remaining message content.
    cleaned = re.sub(
        r"<\s*(?:media omitted|midia oculta|mídia oculta|media oculta|midia omitida|mídia omitida)\s*>",
        "",
        text,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    return cleaned


def home(request):
    context = {
        "stats": {
            "chats": Chat.objects.count(),
            "participants": Participant.objects.count(),
            "contacts": Contact.objects.count(),
            "messages": Message.objects.count(),
            "media_assets": MediaAsset.objects.count(),
        },
        "recent_chats": Chat.objects.annotate(messages_count=Count("messages")).order_by("-created_at")[:10],
    }
    return render(request, "imports/home.html", context)


def chat_list(request):
    chats = Chat.objects.annotate(
        participants_count=Count("participants", distinct=True),
        messages_count=Count("messages", distinct=True),
    ).order_by("title")
    return render(request, "imports/chat_list.html", {"chats": chats})


def chat_detail(request, chat_id: int):
    chat = get_object_or_404(Chat, id=chat_id)
    participants = chat.participants.select_related("contact").prefetch_related("links").order_by("display_name")
    recent_messages = list(
        chat.messages.select_related("participant", "participant__contact")
        .prefetch_related("media_assets")
        .order_by("-timestamp")[:100]
    )[::-1]
    chat_media_assets = list(chat.media_assets.all())
    media_by_normalized_name: dict[str, list[MediaAsset]] = {}
    media_by_sha: dict[str, MediaAsset] = {}
    for media in chat_media_assets:
        key = _normalize_media_name(media.original_name)
        media_by_normalized_name.setdefault(key, []).append(media)
        media_by_sha[media.sha256] = media

    message_cards = []
    for message in recent_messages:
        linked_media = list(message.media_assets.all())
        if not linked_media:
            recovered_by_hash: list[MediaAsset] = []
            seen_ids_by_hash: set[int] = set()
            for sha in (message.media_ref_sha256_map or {}).values():
                media = media_by_sha.get(sha)
                if media and media.id not in seen_ids_by_hash:
                    seen_ids_by_hash.add(media.id)
                    recovered_by_hash.append(media)
            linked_media = recovered_by_hash

        if not linked_media:
            recovered: list[MediaAsset] = []
            seen_ids: set[int] = set()
            for ref in message.media_refs:
                normalized_ref = _normalize_media_name(ref)
                if not normalized_ref:
                    continue
                for media in media_by_normalized_name.get(normalized_ref, []):
                    if media.id not in seen_ids:
                        seen_ids.add(media.id)
                        recovered.append(media)
            linked_media = recovered

        has_unresolved_ref = bool(
            [r for r in message.media_refs if not _is_media_omitted_marker(r)]
        ) and not linked_media
        message_cards.append(
            {
                "message": message,
                "display_text": _clean_message_text_for_display(message.text),
                "media_assets": linked_media,
                "has_unresolved_ref": has_unresolved_ref
                or any(_is_media_omitted_marker(r) for r in message.media_refs),
            }
        )

    return render(
        request,
        "imports/chat_detail.html",
        {
            "chat": chat,
            "participants": participants,
            "message_cards": message_cards,
        },
    )


def contact_lookup(request):
    query = (request.GET.get("q") or "").strip()
    results = find_contact_chat_interactions(query) if query else []
    return render(
        request,
        "imports/contact_lookup.html",
        {
            "query": query,
            "results": results,
        },
    )


def media_asset_content(request, media_id: int):
    media = get_object_or_404(MediaAsset, id=media_id)
    if not media.payload:
        raise Http404("Midia sem payload armazenado")
    response = HttpResponse(bytes(media.payload), content_type=media.mime or "application/octet-stream")
    response["Content-Disposition"] = f'inline; filename="{media.original_name}"'
    return response


@require_POST
def update_participant_contact(request, chat_id: int, participant_id: int):
    participant = get_object_or_404(Participant.objects.select_related("chat", "contact"), id=participant_id, chat_id=chat_id)
    raw_name = request.POST.get("contact_name", "")
    display_name = infer_contact_display_name(raw_name)
    if not display_name:
        return redirect("imports:chat_detail", chat_id=chat_id)

    normalized_name = normalize_contact_name(display_name)
    if not normalized_name:
        return redirect("imports:chat_detail", chat_id=chat_id)

    contact, _ = Contact.objects.get_or_create(
        normalized_name=normalized_name,
        defaults={"display_name": display_name},
    )
    if contact.display_name != display_name:
        contact.display_name = display_name
        contact.save(update_fields=["display_name"])

    if participant.contact_id != contact.id:
        participant.contact = contact
        participant.save(update_fields=["contact"])
    return redirect("imports:chat_detail", chat_id=chat_id)


def _normalize_media_name(value: str) -> str:
    if not value or _is_media_omitted_marker(value):
        return ""
    cleaned = value.strip().strip('"').strip("'").replace("\\", "/")
    basename = cleaned.split("/")[-1]
    return basename.casefold()
