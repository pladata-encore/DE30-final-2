# myapp/forms.py

from django import forms
from .models import YourModel  # YourModel에 맞게 수정

class YourModelForm(forms.ModelForm):
    class Meta:
        model = YourModel  # YourModel에 맞게 수정
        fields = ['name', 'age', 'email']  # 저장할 필드들을 나열
