from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("competitions", "0004_stage_and_discipline_ordering"),
    ]

    operations = [
        migrations.AddField(
            model_name="competitionstage",
            name="requires_nonzero_each_discipline",
            field=models.BooleanField(
                default=False,
                verbose_name="não pode zerar disciplina",
            ),
        ),
        migrations.AddField(
            model_name="competitiondiscipline",
            name="question_count_kind",
            field=models.CharField(
                choices=[
                    ("official", "Oficial"),
                    ("estimated", "Estimativa"),
                ],
                default="official",
                max_length=12,
                verbose_name="origem do número de questões",
            ),
        ),
    ]
