from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("questions", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="questionrecord",
            name="question_number",
            field=models.CharField(
                max_length=220,
                verbose_name="questão",
            ),
        ),
        migrations.AlterField(
            model_name="questionrecord",
            name="question_url",
            field=models.URLField(
                blank=True,
                max_length=500,
                verbose_name="URL da questão",
            ),
        ),
    ]
