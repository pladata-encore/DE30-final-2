from django.conf import settings
from diaryapp.views.badge_views import get_main_badge

user_email = settings.DEFAULT_FROM_EMAIL  # 예시 이메일
# user_email = request.user.email

def main_badge(request):
    main_nickname, main_badge_name, main_badge_image = get_main_badge(user_email)
    return {
        'main_nickname': main_nickname,
        'main_badge_name': main_badge_name,
        'main_badge_image': main_badge_image
    }
