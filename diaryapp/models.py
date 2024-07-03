# diaryapp/models.py
from io import BytesIO
# from django.db import models
from urllib.parse import urljoin
from PIL import Image
from django.urls import reverse
from django.utils import timezone
from djongo import models
import base64

class ImageModel(models.Model):
    diary = models.OneToOneField('AiwriteModel', on_delete=models.CASCADE, related_name='diary_images')
    image_file = models.TextField()  # base64 인코딩된 이미지 문자열을 저장할 필드
    is_representative = models.BooleanField(default=False)

    def save_image(self, image):
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        self.image_file = base64.b64encode(buffered.getvalue()).decode('utf-8')
        #self.image_file_url = reverse('image_detail', args=[self.pk])

    def get_image(self):
        image_data = base64.b64decode(self.image_file)
        image = Image.open(BytesIO(image_data))
        return image

    def __str__(self):
        return f"Image for {self.diary.unique_diary_id}"

class AiwriteModel(models.Model):
    unique_diary_id = models.CharField(max_length=255, unique=True)  # 실제 사용하는 아이디
    user_email = models.EmailField()
    diarytitle = models.CharField(max_length=100, default='제목')
    emotion = models.CharField(max_length=100)
    content = models.TextField(blank=True, null=True)
    place = models.CharField(max_length=100, default='Unknown')
    created_at = models.DateTimeField(auto_now_add=True)
    withfriend = models.CharField(max_length=100, blank=True, null=True)
    images = models.ManyToManyField(ImageModel, related_name='aiwrite_models')
    representative_image = models.OneToOneField('ImageModel', on_delete=models.SET_NULL, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.created_at:
            self.created_at = timezone.now()

        if not self.unique_diary_id:
            self.unique_diary_id = f"{self.created_at.strftime('%Y%m%d%H%M%S')}{self.diarytitle}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.unique_diary_id}"