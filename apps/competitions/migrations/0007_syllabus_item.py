from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("competitions", "0006_discipline_normalized_name"),
    ]

    operations = [
        migrations.CreateModel(
            name="SyllabusItem",
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
                    "item_code",
                    models.CharField(
                        blank=True,
                        help_text="Numeração exatamente como aparece no edital, quando houver.",
                        max_length=40,
                        verbose_name="item / código",
                    ),
                ),
                ("content", models.TextField(verbose_name="conteúdo do edital")),
                (
                    "priority",
                    models.CharField(
                        choices=[("P1", "P1"), ("P2", "P2"), ("P3", "P3")],
                        default="P2",
                        max_length=2,
                        verbose_name="prioridade",
                    ),
                ),
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
                        related_name="syllabus_items",
                        to="competitions.competitiondiscipline",
                        verbose_name="disciplina do concurso",
                    ),
                ),
                (
                    "parent",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="children",
                        to="competitions.syllabusitem",
                        verbose_name="item-pai",
                    ),
                ),
            ],
            options={
                "verbose_name": "item do edital",
                "verbose_name_plural": "itens do edital",
                "ordering": [
                    "competition_discipline__position",
                    "position",
                    "id",
                ],
            },
        ),
    ]
