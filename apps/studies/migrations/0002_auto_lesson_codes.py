from django.db import migrations, models


def renumber_existing_lessons(apps, schema_editor):
    Lesson = apps.get_model("studies", "Lesson")
    lessons = list(Lesson.objects.order_by("id"))

    for lesson in lessons:
        lesson.code = f"TMP-{lesson.pk}"
        lesson.save(update_fields=["code"])

    for index, lesson in enumerate(lessons, start=1):
        lesson.code = f"G{index:04d}"
        lesson.save(update_fields=["code"])


class Migration(migrations.Migration):
    dependencies = [
        ("studies", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            renumber_existing_lessons,
            migrations.RunPython.noop,
        ),
        migrations.RemoveConstraint(
            model_name="lesson",
            name="unique_lesson_code_per_competition_discipline",
        ),
        migrations.AlterField(
            model_name="lesson",
            name="code",
            field=models.CharField(
                blank=True,
                editable=False,
                max_length=20,
                unique=True,
                verbose_name="código",
            ),
        ),
    ]
