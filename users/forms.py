from django import forms
from django.contrib.auth import get_user_model
from django import forms
import hashlib
import urllib.parse
from pymongo import MongoClient

User = get_user_model()


class UserRegistrationForm(forms.ModelForm):
    username = forms.CharField(max_length=150, label='사용자 이름')
    password1 = forms.CharField(widget=forms.PasswordInput, label='비밀번호')
    password2 = forms.CharField(widget=forms.PasswordInput, label='비밀번호 확인')
    gender = forms.CharField(required=False, label='성별')
    nickname = forms.CharField(required=False, label='닉네임')
    email = forms.EmailField(max_length=100, label='이메일')

    class Meta:
        model = User
        fields = ['username', 'email', 'gender', 'nickname']

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("비밀번호가 일치하지 않습니다.")
        return password2

    def save(self, commit=True):

        user = super().save(commit=False)
        if commit:
            user.set_password(self.cleaned_data['password1'])
            user.save()
        else:
            print("Before save:", user.email)
            user.save()
        return user


class LoginForm(forms.Form):
    email = forms.EmailField(max_length=150, label='사용자 이메일')
    password = forms.CharField(widget=forms.PasswordInput, label='비밀번호')