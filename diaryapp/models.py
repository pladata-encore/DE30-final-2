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
from taggit.models import TagBase, TaggedItemBase
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

'''태그 모델'''
# class TagFriend(TagBase):
#     slug = models.SlugField(  # SlugField를 사용하여 slug 필드 정의
#         verbose_name=_('slug'),  # 필드의 verbose_name 설정
#         unique=True,  # 유니크한 값이어야 함
#         max_length=100,  # 최대 길이는 100
#         allow_unicode=True,  # 유니코드 문자 허용
#     )
#     class Meta:
#         verbose_name = _("tag")  # 단수형 이름 설정
#         verbose_name_plural = _("tags")  # 복수형 이름 설정
#
#     def slugify(self, tag, i=None):  # slugify 메서드 재정의
#         return default_slugify(tag, allow_unicode=True)  # 유니코드 허용하여 slug 생성
#
# class Taggedfriend(TaggedItemBase):  # TaggedItemBase 클래스를 상속받는 TaggedPost 모델 정의
#     content_friend = models.ManyToManyField(  # Post 모델과 관계를 맺는 외래키 필드
#         'FriendModel',  # 관련된 모델의 이름
#         on_delete=models.CASCADE,  # 연결된 객체가 삭제될 때 동작 설정
#     )
#
#     tag = models.ManyToManyField(  # TagModel 모델과 관계를 맺는 외래키 필드
#         'TagFriend',  # 관련된 모델의 이름
#         related_name="%(app_label)s_%(class)s_items",  # 역참조 이름 설정
#         on_delete=models.CASCADE,  # 연결된 객체가 삭제될 때 동작 설정
#     )
#     class Meta:
#         verbose_name = _("tagged friend")  # 단수형 이름 설정
#         verbose_name_plural = _("tagged friend")  # 복수형 이름 설정

'''다이어리 모델'''
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

'''댓글 모델'''
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
