from django.db import migrations, models


def assign_question_codes(apps, schema_editor):
    QuestionRecord = apps.get_model("questions", "QuestionRecord")
    for index, record in enumerate(
        QuestionRecord.objects.order_by("id"),
        start=1,
    ):
        record.code = f"Q{index:04d}"
        record.save(update_fields=["code"])


class Migration(migrations.Migration):
    dependencies = [
        ("questions", "0002_expand_question_text_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="questionrecord",
            name="code",
            field=models.CharField(
                blank=True,
                editable=False,
                max_length=20,
                null=True,
                unique=True,
                verbose_name="código",
            ),
        ),
        migrations.RunPython(
            assign_question_codes,
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="questionrecord",
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
