from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("electricity", "0001_initial"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="electricitybill",
            constraint=models.UniqueConstraint(
                fields=("reading",),
                name="unique_electricity_bill_per_reading",
            ),
        ),
    ]
