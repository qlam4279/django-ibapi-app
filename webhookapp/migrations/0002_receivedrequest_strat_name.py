# Generated by Django 4.2.16 on 2024-09-11 13:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("webhookapp", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="receivedrequest",
            name="strat_name",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
