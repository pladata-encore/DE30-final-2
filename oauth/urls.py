from django.urls import path

from oauth.views import *
from users.views import HomeView


urlpatterns = [

    path('naver/login/', NaverLoginView.as_view()),
    path('naver/login/callback/', NaverCallbackView.as_view()),
    path('users/home/', HomeView.as_view(), name='home')
]