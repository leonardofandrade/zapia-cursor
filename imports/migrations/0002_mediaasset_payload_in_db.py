from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("imports", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="mediaasset",
            name="stored_path",
        ),
        migrations.AddField(
            model_name="mediaasset",
            name="payload",
            field=models.BinaryField(default=b""),
            preserve_default=False,
        ),
    ]
