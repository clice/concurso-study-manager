from django.db import migrations, models


def deduplicate_competition_disciplines(apps, schema_editor):
    CompetitionDiscipline = apps.get_model("competitions", "CompetitionDiscipline")
    seen = set()

    for link in CompetitionDiscipline.objects.order_by("competition_id", "position", "id"):
        key = (link.competition_id, link.discipline_id)
        if key in seen:
            link.delete()
        else:
            seen.add(key)


class Migration(migrations.Migration):
    dependencies = [
        ("competitions", "0003_simplify_competition_fields"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="competitionstage",
            name="unique_competition_stage_position",
        ),
        migrations.RemoveField(
            model_name="competitionstage",
            name="name",
        ),
        migrations.AlterField(
            model_name="competitionstage",
            name="stage_type",
            field=models.CharField(
                choices=[
                    ("objective", "Prova objetiva"),
                    ("essay", "Prova discursiva"),
                    ("practical", "Prova prática"),
                    ("titles", "Avaliação de títulos"),
                    ("heteroidentification", "Heteroidentificação"),
                    ("biopsychosocial", "Avaliação biopsicossocial"),
                    ("physical", "Teste de aptidão física"),
                    ("medical", "Avaliação médica"),
                    ("psychological", "Avaliação psicológica"),
                    ("documents", "Verificação documental"),
                    ("training", "Curso de formação"),
                    ("other", "Outra etapa"),
                ],
                default="objective",
                max_length=24,
                verbose_name="etapa",
            ),
        ),
        migrations.AlterField(
            model_name="competitionstage",
            name="position",
            field=models.PositiveIntegerField(default=0, editable=False, verbose_name="posição"),
        ),
        migrations.RemoveConstraint(
            model_name="competitiondiscipline",
            name="unique_competition_stage_discipline",
        ),
        migrations.RemoveField(
            model_name="competitiondiscipline",
            name="stage",
        ),
        migrations.AddField(
            model_name="competitiondiscipline",
            name="minimum_score",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=8,
                null=True,
                verbose_name="pontuação mínima",
            ),
        ),
        migrations.AlterField(
            model_name="competitiondiscipline",
            name="position",
            field=models.PositiveIntegerField(default=0, editable=False, verbose_name="posição"),
        ),
        migrations.RunPython(deduplicate_competition_disciplines, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="competitiondiscipline",
            constraint=models.UniqueConstraint(
                fields=("competition", "discipline"),
                name="unique_competition_discipline",
            ),
        ),
        migrations.AlterModelOptions(
            name="competitiondiscipline",
            options={"ordering": ["position", "discipline__name"]},
        ),
    ]
