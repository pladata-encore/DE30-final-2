# diaryapp/forms.py
from django import forms
from .models import *
from .storage import *


class DiaryForm(forms.ModelForm):
    image_file = forms.FileField(required=False)
    emotion = forms.ChoiceField(choices=AiwriteModel.EMOTION_CHOICES)
    # video_file = forms.FileField(required=False)
    # sticker_file = forms.FileField(required=False)

    class Meta:
        model = AiwriteModel
        fields = ['diarytitle', 'place', 'emotion', 'withfriend', 'content']

    def save(self, commit=True):
        instance = super(DiaryForm, self).save(commit=False)

        # 파일 필드 처리
        image_file = self.cleaned_data.get('image_file')
        # video_file = self.cleaned_data.get('video_file')
        # sticker_file = self.cleaned_data.get('sticker_file')

        if image_file:
            image_file_id = save_file_to_gridfs(image_file.read(), image_file.name)
            image_model = instance.images.create(image_id=image_file_id, is_representative=True)
            image_model.save()

        if commit:
            instance.save()

        return instance


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = [single_file_clean(data, initial)]
        return result

class ImageUploadForm(forms.Form):
    images = MultipleFileField()

    def clean_images(self):
        images = self.cleaned_data.get('images')
        if images:
            for img in images:
                if img.content_type not in ['image/jpeg', 'image/png']:
                    raise forms.ValidationError('Only JPEG and PNG images are allowed.')
                if img.size > 10 * 1024 * 1024:  # 10 MB
                    raise forms.ValidationError('Image file size must be under 10MB.')
        return images

    def save(self, diary_instance):
        images = self.cleaned_data.get('images')
        if images:
            for img in images:
                image_model = ImageModel(diary=diary_instance, is_representative=False)  # 항상 False로 설정
                image_model.save_image(img)
                image_model.save()
