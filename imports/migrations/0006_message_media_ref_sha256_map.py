from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("imports", "0005_contact_and_participant_fk"),
    ]

    operations = [
        migrations.AddField(
            model_name="message",
            name="media_ref_sha256_map",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
