from django.urls import path
from .views import *
from .views import HomeView


app_name = 'users'

urlpatterns = [
    path('home/', HomeView.as_view(), name='home'),
    # path('login', login, name='login'),
    path('login', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('register/', register, name='register'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh')
]