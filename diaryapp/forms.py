from django import forms
from .models import AiwriteModel

# 다이어리 작성
class DiaryForm(forms.ModelForm):
    class Meta:
        model = AiwriteModel
        fields = ['diarytitle', 'place', 'emotion', 'withfriend', 'content', 'image_file', 'video_file', 'sticker_file']

# 다이어리 리스트?
class ListForm(forms.ModelForm):
    class Meta:
        model = AiwriteModel
        fields = ['diarytitle', 'image_file']