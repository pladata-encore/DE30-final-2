# diaryapp/forms.py
from django import forms
from .models import AiwriteModel, ImageModel
from .storage import save_file_to_gridfs, get_file_url_from_gridfs


class DiaryForm(forms.ModelForm):
    image_file = forms.FileField(required=False)
    video_file = forms.FileField(required=False)
    sticker_file = forms.FileField(required=False)

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
            instance.images.create(image_id=image_file_id)

        if commit:
            instance.save()

        return instance

#
# class ListForm(forms.ModelForm):
#     class Meta:
#         model = AiwriteModel
#         fields = ['diarytitle']
