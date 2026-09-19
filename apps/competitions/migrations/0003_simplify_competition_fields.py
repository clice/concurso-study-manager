from django.db import migrations, models
import django.db.models.deletion


DEFAULT_BOARDS = [
    ("Cebraspe", "CEBRASPE"),
    ("Centro Brasileiro de Pesquisa em Avaliação e Seleção e de Promoção de Eventos", "CESPE/UnB"),
    ("Fundação Carlos Chagas", "FCC"),
    ("Fundação Cesgranrio", "CESGRANRIO"),
    ("Fundação Getulio Vargas", "FGV"),
    ("Instituto AOCP", "AOCP"),
    ("Instituto Brasileiro de Formação e Capacitação", "IBFC"),
    ("Instituto Consulplan", "CONSULPLAN"),
    ("Instituto de Desenvolvimento Educacional, Cultural e Assistencial Nacional", "IDECAN"),
    ("Instituto Quadrix", "QUADRIX"),
    ("Vunesp", "VUNESP"),
]


def seed_boards_and_link_existing(apps, schema_editor):
    ExamBoard = apps.get_model("competitions", "ExamBoard")
    Competition = apps.get_model("competitions", "Competition")

    by_acronym = {}
    for name, acronym in DEFAULT_BOARDS:
        board, _ = ExamBoard.objects.get_or_create(acronym=acronym, defaults={"name": name})
        by_acronym[acronym.casefold()] = board

    for competition in Competition.objects.exclude(board=""):
        raw = (competition.board or "").strip()
        board = by_acronym.get(raw.casefold())
        if board is None:
            board, _ = ExamBoard.objects.get_or_create(
                acronym=raw[:40],
                defaults={"name": raw[:180]},
            )
        competition.board_ref_id = board.pk
        competition.save(update_fields=["board_ref"])


class Migration(migrations.Migration):
    dependencies = [
        ("competitions", "0002_competition_registration"),
    ]

    operations = [
        migrations.CreateModel(
            name="ExamBoard",
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
                ("name", models.CharField(max_length=180, unique=True, verbose_name="nome")),
                ("acronym", models.CharField(max_length=40, unique=True, verbose_name="sigla")),
            ],
            options={
                "verbose_name": "banca",
                "verbose_name_plural": "bancas",
                "ordering": ["acronym"],
            },
        ),
        migrations.AddField(
            model_name="competition",
            name="board_ref",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="competitions",
                to="competitions.examboard",
                verbose_name="banca",
            ),
        ),
        migrations.RunPython(seed_boards_and_link_existing, migrations.RunPython.noop),
        migrations.RemoveField(model_name="competition", name="board"),
        migrations.RenameField(
            model_name="competition",
            old_name="board_ref",
            new_name="board",
        ),
        migrations.RemoveField(model_name="competition", name="notice_number"),
        migrations.RemoveField(model_name="competition", name="validity"),
        migrations.AlterField(
            model_name="competition",
            name="fee",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=8,
                null=True,
                verbose_name="taxa de inscrição",
            ),
        ),
        migrations.AlterField(
            model_name="competition",
            name="registration_start",
            field=models.DateField(
                blank=True, null=True, verbose_name="início das inscrições"
            ),
        ),
        migrations.AlterField(
            model_name="competition",
            name="registration_end",
            field=models.DateField(
                blank=True, null=True, verbose_name="fim das inscrições"
            ),
        ),
        migrations.AlterField(
            model_name="competition",
            name="exam_date",
            field=models.DateField(blank=True, null=True, verbose_name="data da prova"),
        ),
        migrations.AlterField(
            model_name="competition",
            name="exam_time",
            field=models.TimeField(blank=True, null=True, verbose_name="horário da prova"),
        ),
    ]
