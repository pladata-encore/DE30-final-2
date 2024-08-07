# Generated by Django 4.1.13 on 2024-07-26 00:41

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("diaryapp", "0005_alter_aiwritemodel_diarytitle_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="aiwritemodel",
            name="diarytitle",
            field=models.CharField(default="제목을 작성해주세요.", max_length=100),
        ),
        migrations.AlterField(
            model_name="aiwritemodel",
            name="place",
            field=models.CharField(default="장소는 일정에서 불러옵니다.", max_length=100),
        ),
        migrations.AlterField(
            model_name="commentmodel",
            name="comment",
            field=models.TextField(blank=True, default="댓글을 작성해주세요.", null=True),
        ),
    ]