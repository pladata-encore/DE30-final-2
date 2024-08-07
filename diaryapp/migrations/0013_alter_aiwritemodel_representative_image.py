# Generated by Django 4.1.13 on 2024-08-05 09:37

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("diaryapp", "0012_alter_aiwritemodel_representative_image"),
    ]

    operations = [
        migrations.AlterField(
            model_name="aiwritemodel",
            name="representative_image",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="diaryapp.imagemodel",
            ),
        ),
    ]
