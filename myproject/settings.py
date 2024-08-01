import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-a&)gx3mp+#9epz5&okvg@x6e*a#z%9%#p(k_uwl7w%bkwcntve'

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']  # 실제 호스트를 추가해야 합니다.

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'djongo',
    'Jpage',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

CSRF_COOKIE_NAME = 'csrftoken'  # CSRF 쿠키 이름 설정
CSRF_COOKIE_SECURE = True       # HTTPS에서만 쿠키 전송
CSRF_COOKIE_HTTPONLY = True     # JavaScript에서 접근 불가
CSRF_HEADER_NAME = 'HTTP_X_CSRFTOKEN'  # CSRF 토큰을 포함할 헤더 이름

ROOT_URLCONF = 'myproject.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'Jpage/templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'myproject.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'djongo',
        'NAME': 'diaryData',
        'ENFORCE_SCHEMA': False,
        'CLIENT': {
            'host': 'mongodb://localhost:27017/',
            'username': 'Hyeonna',
            'password': '010217',
            'authMechanism': 'SCRAM-SHA-1',  # MongoDB 클라우드에 맞는 인증 메커니즘 설정
        }
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

STATIC_URL = '/static/'  # 정적 파일 URL 끝에 슬래시 추가
STATICFILES_DIRS = [
    BASE_DIR / 'Jpage' / 'static',  # 정적 파일이 있는 폴더 경로 설정
]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'