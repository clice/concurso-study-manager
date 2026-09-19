from django.db import migrations, models


def inherit_matching_priorities(apps, schema_editor):
    SyllabusItem = apps.get_model("competitions", "SyllabusItem")

    for item in SyllabusItem.objects.select_related("competition_discipline"):
        if item.priority == item.competition_discipline.priority:
            item.priority = None
            item.save(update_fields=["priority"])


class Migration(migrations.Migration):
    dependencies = [
        ("competitions", "0007_syllabus_item"),
    ]

    operations = [
        migrations.AlterField(
            model_name="syllabusitem",
            name="priority",
            field=models.CharField(
                blank=True,
                choices=[("P1", "P1"), ("P2", "P2"), ("P3", "P3")],
                max_length=2,
                null=True,
                verbose_name="prioridade",
            ),
        ),
        migrations.RunPython(
            inherit_matching_priorities,
            migrations.RunPython.noop,
        ),
    ]
