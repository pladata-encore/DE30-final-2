# diaryapp/models.py
import uuid
from io import BytesIO
# from django.db import models
from urllib.parse import urljoin
from PIL import Image
from django.urls import reverse
from django.utils import timezone
from djongo import models
import base64

class ImageModel(models.Model):
    image_id = models.CharField(max_length=255, unique=True)
    diary = models.ManyToManyField('AiwriteModel', related_name='diary_images')
    image_file = models.TextField()  # base64 인코딩된 이미지 문자열을 저장할 필드
    is_representative = models.BooleanField(default=False)

    def save_image(self, image):
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        self.image_file = base64.b64encode(buffered.getvalue()).decode('utf-8')

    def save(self, *args, **kwargs):
        if not self.image_id:
            self.image_id = str(uuid.uuid4())
        super().save(*args, **kwargs)

    def get_image(self):
        image_data = base64.b64decode(self.image_file)
        image = Image.open(BytesIO(image_data))
        return image

    def __str__(self):
        return f"Image for {self.diary.unique_diary_id}"


class AiwriteModel(models.Model):
    EMOTION_CHOICES = [
        ('null', '없음'),
        ('Happiness', '행복'),
        ('Sadness', '슬픔'),
        ('Anger', '화남'),
        ('Annoyance', '짜증'),
        ('Joy', '기쁨'),
        ('Fear', '두려움 '),
        ('Relief', '안도 '),
        ('Anxiety', '불안  '),
    ]

    unique_diary_id = models.CharField(max_length=255, unique=True)  # 실제 사용하는 아이디
    user_email = models.EmailField()    # user가 생기면 writer 변경
    #writer = models.ManyToManyField('UserModel', related_name='user_models', on_delete=models.SET_NULL, blank=True, null=True)
    diarytitle = models.CharField(max_length=100, default='제목')
    emotion = models.CharField(max_length=100, choices=EMOTION_CHOICES)
    content = models.TextField(blank=True, null=True)
    place = models.CharField(max_length=100, default='Unknown')
    created_at = models.DateTimeField(auto_now_add=True)
    withfriend = models.CharField(max_length=100, blank=True, null=True)
    images = models.ManyToManyField(ImageModel, related_name='aiwrite_models')
    representative_image = models.OneToOneField('ImageModel', on_delete=models.SET_NULL, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.created_at:
            self.created_at = timezone.now()

        if not self.unique_diary_id:
            self.unique_diary_id = f"{self.created_at.strftime('%Y%m%d%H%M%S')}{self.diarytitle}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.unique_diary_id}"

#
# class CommentModel(models.Model):
#     comment_id = models.CharField(max_length=255, unique=True)      # 실제 사용하는 아이디
#     user_email = models.EmailField()
#     comment = models.TextField(blank=True, null=True)
#     badge_id = models.CharField(max_length=255)     # 뱃지 컬렉션에서 가져올 뱃지 아이디
#     diary_id = models.ManyToManyField(AiwriteModel, related_name='aiwrite_models')     # AiwriteModel컬렉션에서 가져올 다이어리 아이디
#     created_at = models.DateTimeField(auto_now_add=True)
#
#     @property
#     def badge_image_data(self):
#         # badge_id를 사용하여 MongoDB에서 뱃지 데이터 가져오기
#         if self.badge_id:
#             badge_data = get_badge_data(self.badge_id)
#             if badge_data and 'image_base64' in badge_data:
#                 return badge_data['image_base64']
#         return None
#
#     @property
#     def diary_data(self):
#         # diary_id를 사용하여 AiwriteModel에서 다이어리 데이터 가져오기
#         if self.diary_id:
#             diary_data = get_diary_data(self.diary_id)
#             return diary_data
#         return None
#
#     def save(self, *args, **kwargs):
#         if not self.created_at:
#             self.created_at = timezone.now()
#
#         if not self.comment_id:
#             self.comment_id = f"{self.created_at.strftime('%Y%m%d%H%M%S')}{self.user_email}"
#
#         super().save(*args, **kwargs)
#
#     def __str__(self):
#         return f"{self.comment_id}"
# def get_badge_data(badge_id):
#     # badge_id로 필터링하여 MongoDB에서 데이터 가져오기
#     badge_data = badge_collection.find_one({'badge_id': badge_id})
#     return badge_data
#
# def get_diary_data(diary_id):
#     try:
#         diary_obj = AiwriteModel.objects.get(diary_id=diary_id)
#         return diary_obj
#     except AiwriteModel.DoesNotExist:
#         return None