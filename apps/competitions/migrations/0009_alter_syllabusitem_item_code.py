from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("competitions", "0008_syllabus_priority_inheritance"),
    ]

    operations = [
        migrations.AlterField(
            model_name="syllabusitem",
            name="item_code",
            field=models.CharField(
                blank=True,
                help_text=(
                    "Deixe vazio para gerar automaticamente. "
                    "Preencha apenas quando precisar preservar uma numeração diferente do edital."
                ),
                max_length=40,
                verbose_name="item / código",
            ),
        ),
    ]
