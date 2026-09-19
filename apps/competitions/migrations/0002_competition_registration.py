from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("competitions", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="competition",
            name="name",
            field=models.CharField(max_length=200, verbose_name="nome do concurso"),
        ),
        migrations.AlterField(
            model_name="competition",
            name="organization",
            field=models.CharField(max_length=180, verbose_name="órgão"),
        ),
        migrations.AlterField(
            model_name="competition",
            name="role",
            field=models.CharField(max_length=200, verbose_name="cargo"),
        ),
        migrations.AlterField(
            model_name="competition",
            name="exam_date",
            field=models.DateField(
                blank=True, null=True, verbose_name="data principal da prova"
            ),
        ),
        migrations.AlterField(
            model_name="competition",
            name="exam_time",
            field=models.TimeField(
                blank=True, null=True, verbose_name="horário principal da prova"
            ),
        ),
        migrations.AddField(
            model_name="competition",
            name="validity",
            field=models.CharField(blank=True, max_length=220, verbose_name="validade"),
        ),
        migrations.AddField(
            model_name="competition",
            name="location",
            field=models.CharField(blank=True, max_length=220, verbose_name="localidade"),
        ),
        migrations.CreateModel(
            name="CompetitionStage",
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
                ("name", models.CharField(max_length=180, verbose_name="nome da etapa")),
                (
                    "stage_type",
                    models.CharField(
                        choices=[
                            ("objective", "Prova objetiva"),
                            ("essay", "Prova discursiva"),
                            ("practical", "Prova prática"),
                            ("titles", "Avaliação de títulos"),
                            ("physical", "Teste de aptidão física"),
                            ("medical", "Avaliação médica"),
                            ("psychological", "Avaliação psicológica"),
                            ("documents", "Verificação documental"),
                            ("training", "Curso de formação"),
                            ("other", "Outra etapa"),
                        ],
                        default="objective",
                        max_length=24,
                        verbose_name="tipo",
                    ),
                ),
                (
                    "position",
                    models.PositiveIntegerField(
                        default=1,
                        help_text="Ordem em que a etapa aparece no concurso.",
                        verbose_name="posição",
                    ),
                ),
                (
                    "scheduled_date",
                    models.DateField(blank=True, null=True, verbose_name="data"),
                ),
                (
                    "scheduled_time",
                    models.TimeField(blank=True, null=True, verbose_name="horário"),
                ),
                ("eliminatory", models.BooleanField(default=True, verbose_name="eliminatória")),
                (
                    "classificatory",
                    models.BooleanField(default=True, verbose_name="classificatória"),
                ),
                (
                    "max_score",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=8,
                        null=True,
                        verbose_name="pontuação máxima",
                    ),
                ),
                (
                    "minimum_score",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=8,
                        null=True,
                        verbose_name="pontuação mínima",
                    ),
                ),
                ("details", models.TextField(blank=True, verbose_name="detalhes / critérios")),
                (
                    "competition",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="stages",
                        to="competitions.competition",
                    ),
                ),
            ],
            options={
                "verbose_name": "etapa do concurso",
                "verbose_name_plural": "etapas do concurso",
                "ordering": ["position", "id"],
            },
        ),
        migrations.RemoveConstraint(
            model_name="competitiondiscipline",
            name="unique_competition_discipline",
        ),
        migrations.RenameField(
            model_name="competitiondiscipline",
            old_name="order",
            new_name="position",
        ),
        migrations.AlterField(
            model_name="competitiondiscipline",
            name="competition",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="discipline_links",
                to="competitions.competition",
            ),
        ),
        migrations.AlterField(
            model_name="competitiondiscipline",
            name="knowledge_area",
            field=models.CharField(
                choices=[
                    ("general", "Conhecimentos Gerais"),
                    ("specific", "Conhecimentos Específicos"),
                ],
                max_length=16,
                verbose_name="grupo",
            ),
        ),
        migrations.AlterField(
            model_name="competitiondiscipline",
            name="priority",
            field=models.CharField(
                choices=[("P1", "P1"), ("P2", "P2"), ("P3", "P3")],
                default="P2",
                max_length=2,
                verbose_name="prioridade",
            ),
        ),
        migrations.AlterField(
            model_name="competitiondiscipline",
            name="expected_questions",
            field=models.PositiveIntegerField(
                blank=True, null=True, verbose_name="número de questões"
            ),
        ),
        migrations.AlterField(
            model_name="competitiondiscipline",
            name="weight",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=5,
                null=True,
                verbose_name="peso",
            ),
        ),
        migrations.AlterField(
            model_name="competitiondiscipline",
            name="position",
            field=models.PositiveIntegerField(
                default=1,
                help_text="Ordem de exibição dentro da etapa.",
                verbose_name="posição",
            ),
        ),
        migrations.AddField(
            model_name="competitiondiscipline",
            name="max_score",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=8,
                null=True,
                verbose_name="pontuação máxima",
            ),
        ),
        migrations.AddField(
            model_name="competitiondiscipline",
            name="stage",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="discipline_links",
                to="competitions.competitionstage",
            ),
        ),
        migrations.AddConstraint(
            model_name="competitionstage",
            constraint=models.UniqueConstraint(
                fields=("competition", "position"),
                name="unique_competition_stage_position",
            ),
        ),
        migrations.RunSQL(
            sql="""
                INSERT INTO competitions_competitionstage
                    (name, stage_type, position, eliminatory, classificatory, details, competition_id)
                SELECT
                    'Prova objetiva',
                    'objective',
                    1,
                    1,
                    1,
                    '',
                    c.id
                FROM competitions_competition c
                WHERE EXISTS (
                    SELECT 1
                    FROM competitions_competitiondiscipline cd
                    WHERE cd.competition_id = c.id
                )
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql="""
                UPDATE competitions_competitiondiscipline
                SET stage_id = (
                    SELECT s.id
                    FROM competitions_competitionstage s
                    WHERE s.competition_id = competitions_competitiondiscipline.competition_id
                      AND s.position = 1
                    LIMIT 1
                )
                WHERE stage_id IS NULL
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.AlterField(
            model_name="competitiondiscipline",
            name="stage",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="discipline_links",
                to="competitions.competitionstage",
            ),
        ),
        migrations.AddConstraint(
            model_name="competitiondiscipline",
            constraint=models.UniqueConstraint(
                fields=("competition", "stage", "discipline"),
                name="unique_competition_stage_discipline",
            ),
        ),
        migrations.AlterModelOptions(
            name="competitiondiscipline",
            options={
                "ordering": ["stage__position", "position", "discipline__name"]
            },
        ),
    ]
