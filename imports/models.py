from django.db import models


class ImportJob(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    arquivo_original = models.CharField(max_length=255)
    sha256_zip = models.CharField(max_length=64, unique=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    summary_json = models.JSONField(default=dict, blank=True)

    def __str__(self) -> str:
        return f"{self.arquivo_original} ({self.status})"


class Chat(models.Model):
    title = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.title


class Participant(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name="participants")
    display_name = models.CharField(max_length=255)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["chat", "display_name"], name="uniq_participant_per_chat")
        ]

    def __str__(self) -> str:
        return f"{self.chat.title}::{self.display_name}"


class ParticipantLink(models.Model):
    participant = models.ForeignKey(
        Participant, on_delete=models.CASCADE, related_name="links"
    )
    label = models.CharField(max_length=120, blank=True)
    url = models.URLField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["participant", "url"], name="uniq_participant_link_url"
            )
        ]
        indexes = [models.Index(fields=["participant", "created_at"])]

    def __str__(self) -> str:
        return f"{self.participant.display_name}::{self.url}"


class Message(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name="messages")
    participant = models.ForeignKey(
        Participant, on_delete=models.SET_NULL, null=True, blank=True, related_name="messages"
    )
    timestamp = models.DateTimeField()
    text = models.TextField(blank=True)
    is_system = models.BooleanField(default=False)
    content_hash = models.CharField(max_length=64)
    raw_line = models.TextField(blank=True)
    media_refs = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["chat", "timestamp"]),
            models.Index(fields=["content_hash"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["chat", "participant", "timestamp", "content_hash"],
                name="uniq_message_identity",
            )
        ]

    def __str__(self) -> str:
        sender = self.participant.display_name if self.participant else "system"
        return f"{self.chat.title}@{self.timestamp.isoformat()}::{sender}"


class MediaAsset(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name="media_assets")
    message = models.ForeignKey(
        Message, on_delete=models.SET_NULL, null=True, blank=True, related_name="media_assets"
    )
    original_name = models.CharField(max_length=255)
    sha256 = models.CharField(max_length=64, unique=True)
    payload = models.BinaryField()
    mime = models.CharField(max_length=100, blank=True)
    size_bytes = models.PositiveBigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["chat", "original_name"])]

    def __str__(self) -> str:
        return f"{self.original_name} ({self.sha256[:8]})"
