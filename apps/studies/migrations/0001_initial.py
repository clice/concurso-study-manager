# Generated manually for the first studies schema.
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("competitions", "0010_remove_syllabus_item_priority"),
    ]

    operations = [
        migrations.CreateModel(
            name="Lesson",
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
                (
                    "code",
                    models.CharField(
                        blank=True,
                        help_text="Identificador da aula no curso, por exemplo G588.",
                        max_length=40,
                        verbose_name="código",
                    ),
                ),
                ("title", models.CharField(max_length=300, verbose_name="título")),
                (
                    "macrotheme",
                    models.CharField(blank=True, max_length=220, verbose_name="macrotema"),
                ),
                (
                    "source",
                    models.CharField(
                        blank=True,
                        default="Gran Cursos Online",
                        max_length=120,
                        verbose_name="fonte",
                    ),
                ),
                ("video_url", models.URLField(blank=True, verbose_name="videoaula")),
                (
                    "transcript_url",
                    models.URLField(blank=True, verbose_name="degravação"),
                ),
                ("handout_url", models.URLField(blank=True, verbose_name="apostila")),
                (
                    "suggested_week",
                    models.PositiveIntegerField(
                        blank=True,
                        null=True,
                        verbose_name="semana sugerida",
                    ),
                ),
                (
                    "planned_date",
                    models.DateField(blank=True, null=True, verbose_name="data planejada"),
                ),
                (
                    "studied_date",
                    models.DateField(blank=True, null=True, verbose_name="data estudada"),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("not_started", "Não iniciada"),
                            ("in_progress", "Em andamento"),
                            ("completed", "Concluída"),
                        ],
                        default="not_started",
                        max_length=20,
                        verbose_name="status",
                    ),
                ),
                (
                    "questions_done",
                    models.PositiveIntegerField(
                        blank=True,
                        null=True,
                        verbose_name="questões feitas",
                    ),
                ),
                (
                    "correct_answers",
                    models.PositiveIntegerField(
                        blank=True,
                        null=True,
                        verbose_name="acertos",
                    ),
                ),
                ("notes", models.TextField(blank=True, verbose_name="observações")),
                (
                    "position",
                    models.PositiveIntegerField(
                        default=0,
                        editable=False,
                        verbose_name="posição",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "competition_discipline",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="lessons",
                        to="competitions.competitiondiscipline",
                        verbose_name="disciplina",
                    ),
                ),
                (
                    "syllabus_items",
                    models.ManyToManyField(
                        blank=True,
                        related_name="lessons",
                        to="competitions.syllabusitem",
                        verbose_name="itens do edital",
                    ),
                ),
            ],
            options={
                "verbose_name": "aula",
                "verbose_name_plural": "aulas",
                "ordering": [
                    "competition_discipline__position",
                    "position",
                    "id",
                ],
            },
        ),
        migrations.AddConstraint(
            model_name="lesson",
            constraint=models.UniqueConstraint(
                condition=models.Q(("code", ""), _negated=True),
                fields=("competition_discipline", "code"),
                name="unique_lesson_code_per_competition_discipline",
            ),
        ),
    ]
