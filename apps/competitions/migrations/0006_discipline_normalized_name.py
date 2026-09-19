import unicodedata

from django.db import migrations, models


def normalize_name(value):
    normalized = unicodedata.normalize("NFKC", value or "")
    return " ".join(normalized.split()).casefold()


def populate_normalized_names(apps, schema_editor):
    Discipline = apps.get_model("competitions", "Discipline")
    seen = {}

    for discipline in Discipline.objects.order_by("id"):
        normalized = normalize_name(discipline.name)
        if normalized in seen:
            raise RuntimeError(
                "Existem disciplinas duplicadas após normalização Unicode: "
                f"{seen[normalized]!r} e {discipline.name!r}."
            )
        seen[normalized] = discipline.name
        discipline.normalized_name = normalized
        discipline.save(update_fields=["normalized_name"])


class Migration(migrations.Migration):
    dependencies = [
        ("competitions", "0005_approval_rules_and_estimates"),
    ]

    operations = [
        migrations.AddField(
            model_name="discipline",
            name="normalized_name",
            field=models.CharField(
                blank=True,
                editable=False,
                max_length=160,
                null=True,
            ),
        ),
        migrations.RunPython(populate_normalized_names, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="discipline",
            name="normalized_name",
            field=models.CharField(
                editable=False,
                max_length=160,
                unique=True,
            ),
        ),
    ]
