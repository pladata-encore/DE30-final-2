from django.conf import settings
from django.db import models
from djongo import models
from django.utils import timezone
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin
import hashlib

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

from djongo import models

class UserModel(AbstractBaseUser, PermissionsMixin, models.Model):
    email = models.EmailField(max_length=100, unique=True, verbose_name='이메일', blank=False, null=False, primary_key=True)
    username = models.CharField(max_length=150, unique=True, verbose_name='사용자 이름', blank=False, null=False)
    gender = models.CharField(max_length=10, blank=True, verbose_name='성별')  # null=True 제거
    nickname = models.CharField(max_length=100, blank=True, verbose_name='닉네임')  # null=True 제거
    register_id = models.CharField(max_length=255, unique=True, blank=True,verbose_name='등록 ID')
    # isSocial = models.CharField(max_length=1, default='0')  # CharField로 정의

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def save(self, *args, **kwargs):
        if not self.register_id:
            self.register_id = hashlib.sha256(self.email.encode()).hexdigest()
        super().save(*args, **kwargs)


    def __str__(self):
        return f'{self.username} ({self.email})'


class UserRoleModel(models.Model):
    role_name = models.CharField(max_length=255, default='default_role')

    def __str__(self):
        return self.role_name