# Initial schema for the competitions module.

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Competition",
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
                ("name", models.CharField(max_length=200)),
                ("organization", models.CharField(max_length=180)),
                ("role", models.CharField(max_length=200)),
                ("board", models.CharField(blank=True, max_length=120, verbose_name="banca")),
                (
                    "notice_number",
                    models.CharField(blank=True, max_length=120, verbose_name="edital"),
                ),
                (
                    "initial_salary",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=12,
                        null=True,
                        verbose_name="salário inicial",
                    ),
                ),
                ("benefits", models.TextField(blank=True, verbose_name="benefícios")),
                (
                    "registration_start",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="início das inscrições"
                    ),
                ),
                (
                    "registration_end",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="fim das inscrições"
                    ),
                ),
                (
                    "exam_date",
                    models.DateField(blank=True, null=True, verbose_name="data da prova"),
                ),
                (
                    "exam_time",
                    models.TimeField(blank=True, null=True, verbose_name="horário da prova"),
                ),
                (
                    "fee",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=8,
                        null=True,
                        verbose_name="taxa",
                    ),
                ),
                ("official_url", models.URLField(blank=True, verbose_name="URL oficial")),
                ("notes", models.TextField(blank=True, verbose_name="observações")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("planned", "Planejado"),
                            ("active", "Em estudo"),
                            ("completed", "Concluído"),
                            ("archived", "Arquivado"),
                        ],
                        default="planned",
                        max_length=20,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "concurso",
                "verbose_name_plural": "concursos",
                "ordering": ["exam_date", "name"],
            },
        ),
        migrations.CreateModel(
            name="Discipline",
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
                ("name", models.CharField(max_length=160, unique=True)),
            ],
            options={
                "verbose_name": "disciplina",
                "verbose_name_plural": "disciplinas",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="CompetitionDiscipline",
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
                    "knowledge_area",
                    models.CharField(
                        choices=[
                            ("general", "Conhecimentos Gerais"),
                            ("specific", "Conhecimentos Específicos"),
                        ],
                        max_length=16,
                    ),
                ),
                (
                    "priority",
                    models.CharField(
                        choices=[("P1", "P1"), ("P2", "P2"), ("P3", "P3")],
                        default="P2",
                        max_length=2,
                    ),
                ),
                ("expected_questions", models.PositiveIntegerField(blank=True, null=True)),
                (
                    "weight",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=5, null=True
                    ),
                ),
                ("order", models.PositiveIntegerField(default=0)),
                (
                    "competition",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="competitions.competition",
                    ),
                ),
                (
                    "discipline",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="competitions.discipline",
                    ),
                ),
            ],
            options={
                "ordering": ["order", "discipline__name"],
            },
        ),
        migrations.AddField(
            model_name="competition",
            name="disciplines",
            field=models.ManyToManyField(
                related_name="competitions",
                through="competitions.CompetitionDiscipline",
                to="competitions.discipline",
            ),
        ),
        migrations.AddConstraint(
            model_name="competitiondiscipline",
            constraint=models.UniqueConstraint(
                fields=("competition", "discipline"),
                name="unique_competition_discipline",
            ),
        ),
    ]
