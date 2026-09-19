from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("studies", "0002_auto_lesson_codes"),
    ]

    operations = [
        migrations.AddField(
            model_name="lesson",
            name="source_reference",
            field=models.CharField(
                blank=True,
                editable=False,
                max_length=40,
                null=True,
                unique=True,
                verbose_name="referência de origem",
            ),
        ),
    ]
