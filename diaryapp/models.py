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
from taggit.managers import TaggableManager
from taggit.models import TagBase, TaggedItemBase, TaggedItem
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify as default_slugify

'''이미지 모델'''
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

'''다이어리-일정 모델'''
class DiaryPlanModel(models.Model):
    unique_diary_id = models.OneToOneField('AiwriteModel', on_delete=models.SET_NULL, blank=True, null=True)

'''다이어리 모델'''
class AiwriteModel(models.Model):
    EMOTION_CHOICES = [
        ('null', '없음'),
        ('Happiness', '행복'),
        ('Joy', '기쁨'),
        ('Fun', '즐거움 '),
        ('Relief', '안도 '),
        ('Excitement', '신남'),
        ('Sadness', '슬픔'),
        ('Anger', '화남'),
        ('Annoyance', '짜증'),
    ]

    unique_diary_id = models.CharField(max_length=255, unique=True)  # 실제 사용하는 아이디
    user_email = models.EmailField()    # user가 생기면 writer 변경
    # writer = models.ManyToManyField(UserModel, related_name='user_models', on_delete=models.SET_NULL, blank=True, null=True)
    diarytitle = models.CharField(max_length=100, default='제목')
    emotion = models.CharField(max_length=100, choices=EMOTION_CHOICES)
    content = models.TextField(blank=True, null=True)
    place = models.CharField(max_length=100, default='Unknown')
    created_at = models.DateTimeField(auto_now_add=True)
    withfriend = models.CharField(max_length=100, blank=True, null=True)
    # tags = TaggableManager(
    #     blank=True,
    # )
    # friends = models.ManyToManyField(User, related_name="tagged_friends")
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

    # def get_tagged_user(self):
    #     tagged_users = []
    #     tagged_items = TaggedItem.objects.filter(content_object=self)
    #
    #     for tagged_item in tagged_items:
    #         if tagged_item.tag.name.startswith('@'):
    #             username = tagged_item.tag.name[1:]  # @ 제거
    #             try:
    #                 user = User.objects.get(username=username)
    #                 tagged_users.append(user)
    #             except User.DoesNotExist:
    #                 # 해당 사용자가 존재하지 않는 경우
    #                 pass
    #
    #     return tagged_users

    # def get_comments(self):
    #     return self.comments.all()

'''댓글 모델'''
class CommentModel(models.Model):
    comment_id = models.CharField(max_length=255, unique=True)      # 실제 사용하는 아이디
    user_email = models.EmailField()
    # author = models.ManyToManyField(UserModel, related_name='user_models')
    diary_id = models.ManyToManyField('AiwriteModel', related_name='diary_comments')
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.created_at:
            self.created_at = timezone.now()

        if not self.comment_id:
            self.comment_id = f"{self.created_at.strftime('%Y%m%d%H%M%S')}{self.user_email}"

        super().save(*args, **kwargs)

    # def __str__(self):
    #     return f'{self.user.username}의 댓글 - {self.diary_id.unique_diary_id}'

    def __str__(self):
        return f'{self.user_email}의 댓글 - {self.diary_id.unique_diary_id}'

    # def can_delete(self, user):
    #     return user == self.user
    def can_delete(self, user):
        return user == self.user_email