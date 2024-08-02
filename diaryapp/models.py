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
    image_id = models.CharField(max_length=255, unique=True)    # image모델
    diary = models.ManyToManyField('AiwriteModel', related_name='diary_images')   # 다이어리 일기 매핑
    image_file = models.TextField()  # base64 인코딩된 이미지 문자열을 저장할 필드
    is_representative = models.BooleanField(default=False)  # 대표 이미지 여부

    def save_image(self, image):    # 이미지 인코딩
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        self.image_file = base64.b64encode(buffered.getvalue()).decode('utf-8')

    def save(self, *args, **kwargs):    # 이미지 아이디 생성
        if not self.image_id:
            self.image_id = str(uuid.uuid4())
        super().save(*args, **kwargs)

    def get_image(self):    # 이미지 디코딩
        image_data = base64.b64decode(self.image_file)
        image = Image.open(BytesIO(image_data))
        return image

'''다이어리-일정 모델'''
class DiaryPlanModel(models.Model):
    unique_diary_id = models.OneToOneField('AiwriteModel', on_delete=models.SET_NULL, blank=True, null=True)
    destination = models.CharField(max_length=255, blank=True, null=True)  # 여행지 정보 저장

    def __str__(self):
        return f"Plan for Diary ID {self.unique_diary_id}"

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
    # writer = models.CharField(max_length=255, blank=True, null=True)
    diarytitle = models.CharField(max_length=100, default='제목을 작성해주세요.')
    emotion = models.CharField(max_length=100, choices=EMOTION_CHOICES)
    content = models.TextField(blank=True, null=True)
    place = models.CharField(max_length=100, default='장소는 일정에서 불러옵니다.')
    created_at = models.DateTimeField(auto_now_add=True)
    withfriend = models.CharField(max_length=100, blank=True, null=True)
    images = models.ManyToManyField(ImageModel, related_name='aiwrite_models')
    representative_image = models.OneToOneField('ImageModel', on_delete=models.SET_NULL, blank=True, null=True)
    nickname_id = models.CharField(max_length=100, null=True, blank=True)
    def save(self, *args, **kwargs):
        if not self.created_at:
            self.created_at = timezone.now()
        if not self.unique_diary_id:
            self.unique_diary_id = f"{self.created_at.strftime('%Y%m%d%H%M%S')}{self.diarytitle}"
        super().save(*args, **kwargs)
    def __str__(self):
        return f"{self.unique_diary_id}"


'''댓글 모델'''
class CommentModel(models.Model):
    comment_id = models.CharField(max_length=255, unique=True)      # 실제 사용하는 아이디
    user_email = models.EmailField()
    # author = models.ManyToManyField(UserModel, related_name='user_models')
    diary_id = models.ManyToManyField('AiwriteModel', related_name='diary_comments')
    comment = models.TextField(blank=True, null=True, default='댓글을 작성해주세요.')
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

'''찜모델'''
class Wishlist(models.Model):
    user_email = models.EmailField()
    place = models.CharField(max_length=2000)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user_email', 'place')  # 'user'를 'user_email'로 변경

    def __str__(self):
        return f"{self.place} - {self.user_email}"



# 플래그 모델(commands 중복 방지)
class CommandFlag(models.Model):
    name = models.CharField(max_length=100, unique=True)
    executed = models.BooleanField(default=False)


# 삭제 예정 (24.07.25 윤보라)
# nickname = models.OneToOneField('Nickname', on_delete=models.SET_NULL, null=True, blank=True, related_name='nickname_model')
# 카테고리1 모델
# class CategoryCode1(models.Model):
#     code = models.CharField(max_length=50, unique=True)
#     name = models.CharField(max_length=255)
#     rnum = models.IntegerField()
#
#     def __str__(self):
#         return self.code
#
#     class Meta:
#         db_table = 'categoryCode1'
# 카테고리3 모델
# class CategoryCode3(models.Model):
#     code = models.CharField(max_length=50, unique=True)
#     name = models.CharField(max_length=255)
#     rnum = models.IntegerField()
#     cat1_code = models.CharField(max_length=50)
#     cat2_code = models.CharField(max_length=50)
#
#     def __str__(self):
#         return self.code
#
#     class Meta:
#         db_table = 'categoryCode3'
# # 뱃지 모델
# class Badge(models.Model):
#     badge_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, primary_key=True)
#     name = models.CharField(max_length=255)
#     badge = models.BinaryField()
#     categoryCode1 = models.CharField(max_length=50, blank=True, null=True)
#     categoryCode3 = models.CharField(max_length=50, blank=True, null=True)
#
#     class Meta:
#         db_table = 'diaryapp_badge'
#
#     def __str__(self):
#         return self.name
# 별명 모델
# class Nickname(models.Model):
#     nickname_id = models.UUIDField(default=uuid.uuid4, editable=False)
#     nickname = models.CharField(max_length=255)
#     unique_diary_id = models.OneToOneField('AiwriteModel', on_delete=models.SET_NULL, null=True, blank=True, related_name='aiwrite_model')
#     badge = models.BinaryField()  # 임베딩 필드
#     title = models.CharField(max_length=255)
#
#     class Meta:
#         db_table = 'nickname'