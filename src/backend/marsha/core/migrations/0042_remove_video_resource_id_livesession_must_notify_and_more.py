# Generated by Django 4.0.3 on 2022-04-08 10:59

from django.conf import settings
import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0041_livesession_registered_at"),
    ]

    operations = [
        migrations.AddField(
            model_name="livesession",
            name="must_notify",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(max_length=200),
                blank=True,
                default=list,
                help_text="List of new notifications to send",
                size=None,
                verbose_name="List of new notifications to send",
            ),
        ),
    ]
