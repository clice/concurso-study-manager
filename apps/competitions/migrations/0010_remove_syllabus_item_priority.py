from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("competitions", "0009_alter_syllabusitem_item_code"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="syllabusitem",
            name="priority",
        ),
    ]
