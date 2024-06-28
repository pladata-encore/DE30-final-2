# from django.db import models
from django.utils import timezone
from djongo import models


class AiwriteModel(models.Model):
    user_email = models.EmailField()
    diarytitle = models.CharField(max_length=100, default='제목')
    emotion = models.CharField(max_length=100)
    content = models.TextField(blank=True, null=True)
    place = models.CharField(max_length=100, default='Unknown')
    image_file = models.ImageField(upload_to='images/', blank=True, null=True)
    video_file = models.FileField(upload_to='videos/', blank=True, null=True)
    sticker_file = models.ImageField(upload_to='stickers', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    withfriend = models.CharField(max_length=100, blank=True, null=True)
    unique_diary_id = models.CharField(max_length=255, unique=True)  # 실제 필드로 추가

    def save(self, *args, **kwargs):
        # created_at 필드가 None일 경우에 현재 시간으로 설정
        if not self.created_at:
            self.created_at = timezone.now()

        # unique_diary_id 필드를 자동으로 생성
        if not self.unique_diary_id:
            self.unique_diary_id = f"{self.created_at.strftime('%Y%m%d%H%M%S')}{self.diarytitle}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.unique_diary_id}"