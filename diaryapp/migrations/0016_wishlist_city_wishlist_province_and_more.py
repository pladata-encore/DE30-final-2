# Generated by Django 4.1.13 on 2024-08-06 07:00

from django.db import migrations, models
import djongo.models.fields


class Migration(migrations.Migration):
    dependencies = [
        ("diaryapp", "0015_aiwritemodel_place"),
    ]

    operations = [
        migrations.AddField(
            model_name="wishlist",
            name="city",
            field=models.CharField(default="Unknown", max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="wishlist",
            name="province",
            field=models.CharField(default="Unknown", max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="wishlist",
            name="travel_dates",
            field=djongo.models.fields.JSONField(default="Unknown"),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="wishlist",
            name="place",
            field=models.CharField(max_length=255),
        ),
    ]