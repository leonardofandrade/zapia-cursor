from django.db.models import Count
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, render

from imports.models import Chat, Contact, MediaAsset, Message, Participant
from imports.services.contact_lookup import find_contact_chat_interactions


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
        chat.messages.select_related("participant")
        .prefetch_related("media_assets")
        .order_by("-timestamp")[:100]
    )[::-1]
    return render(
        request,
        "imports/chat_detail.html",
        {
            "chat": chat,
            "participants": participants,
            "recent_messages": recent_messages,
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
