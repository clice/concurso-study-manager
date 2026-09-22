from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("competitions", "0010_remove_syllabus_item_priority"),
        ("studies", "0003_lesson_source_reference"),
    ]

    operations = [
        migrations.CreateModel(
            name="QuestionRecord",
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
                    "source_reference",
                    models.CharField(
                        blank=True,
                        editable=False,
                        max_length=64,
                        null=True,
                        unique=True,
                        verbose_name="referência de origem",
                    ),
                ),
                ("answered_date", models.DateField(verbose_name="data")),
                ("board", models.CharField(blank=True, max_length=120, verbose_name="banca")),
                (
                    "exam_context",
                    models.CharField(
                        blank=True,
                        max_length=300,
                        verbose_name="órgão / prova / cargo",
                    ),
                ),
                ("question_number", models.CharField(max_length=120, verbose_name="questão")),
                (
                    "topic_subtopic",
                    models.CharField(
                        blank=True,
                        max_length=500,
                        verbose_name="tema / subtema",
                    ),
                ),
                ("user_answer", models.CharField(blank=True, max_length=300, verbose_name="resposta")),
                ("answer_key", models.CharField(blank=True, max_length=300, verbose_name="gabarito")),
                (
                    "result",
                    models.CharField(
                        choices=[
                            ("correct", "Acerto"),
                            ("incorrect", "Erro"),
                            ("not_counted", "Não contabilizar"),
                        ],
                        max_length=20,
                        verbose_name="resultado",
                    ),
                ),
                ("source", models.CharField(blank=True, max_length=500, verbose_name="fonte")),
                ("observation", models.TextField(blank=True, verbose_name="observação")),
                ("review_required", models.BooleanField(default=False, verbose_name="revisar?")),
                ("last_review", models.DateField(blank=True, null=True, verbose_name="última revisão")),
                ("next_review", models.DateField(blank=True, null=True, verbose_name="próxima revisão")),
                (
                    "review_status",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("pending", "Pendente"),
                            ("completed", "Concluída"),
                        ],
                        max_length=20,
                        null=True,
                        verbose_name="status da revisão",
                    ),
                ),
                ("question_url", models.URLField(blank=True, verbose_name="URL da questão")),
                (
                    "url_pending",
                    models.BooleanField(
                        default=False,
                        verbose_name="URL pendente de identificação",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "competition_discipline",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="question_records",
                        to="competitions.competitiondiscipline",
                        verbose_name="disciplina",
                    ),
                ),
                (
                    "lesson",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="question_records",
                        to="studies.lesson",
                        verbose_name="aula",
                    ),
                ),
            ],
            options={
                "verbose_name": "questão respondida",
                "verbose_name_plural": "questões respondidas",
                "ordering": ["-answered_date", "-id"],
            },
        ),
    ]
