# diaryapp/models.py
# from django.db import models
from urllib.parse import urljoin
from django.utils import timezone
from djongo import models
from myproject import settings
from uuid import uuid4

class ImageModel(models.Model):
    # id = models.AutoField(primary_key=True)
    image_id = models.CharField(max_length=255, unique=True)
    image_file_url = models.URLField(max_length=255, null=True, blank=True)
    # diary = models.ForeignKey('AiwriteModel', related_name='images', on_delete=models.CASCADE)  # 일기와의 관계

    def __str__(self):
        return f"Image {self.image_file_url}"

class AiwriteModel(models.Model):
    user_email = models.EmailField()
    diarytitle = models.CharField(max_length=100, default='제목')
    emotion = models.CharField(max_length=100)
    content = models.TextField(blank=True, null=True)
    place = models.CharField(max_length=100, default='Unknown')
    created_at = models.DateTimeField(auto_now_add=True)
    withfriend = models.CharField(max_length=100, blank=True, null=True)
    unique_diary_id = models.CharField(max_length=255, unique=True)  # 실제 필드로 추가
    images = models.ManyToManyField(ImageModel, related_name='aiwrite_images')
    representative_image = models.ForeignKey('ImageModel', on_delete=models.SET_NULL, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.created_at:
            self.created_at = timezone.now()

        if not self.unique_diary_id:
            self.unique_diary_id = f"{self.created_at.strftime('%Y%m%d%H%M%S')}{self.diarytitle}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.unique_diary_id}"