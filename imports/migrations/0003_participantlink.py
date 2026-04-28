import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("imports", "0002_mediaasset_payload_in_db"),
    ]

    operations = [
        migrations.CreateModel(
            name="ParticipantLink",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("label", models.CharField(blank=True, max_length=120)),
                ("url", models.URLField(max_length=500)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "participant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="links",
                        to="imports.participant",
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="participantlink",
            constraint=models.UniqueConstraint(
                fields=("participant", "url"), name="uniq_participant_link_url"
            ),
        ),
        migrations.AddIndex(
            model_name="participantlink",
            index=models.Index(
                fields=["participant", "created_at"],
                name="imports_par_partici_5f1afe_idx",
            ),
        ),
    ]
