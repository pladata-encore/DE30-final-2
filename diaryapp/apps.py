import open_clip
from django.apps import AppConfig

from .clip_model import load_model

class DiaryappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'diaryapp'

# class AiwriteConfig(AppConfig):
#     default_auto_field = "django.db.models.BigAutoField"
#     name = "diaryapp"

# CLIP모델
    def ready(self):
        load_model()