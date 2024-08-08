from django.contrib.auth.backends import BaseBackend
from users.models import UserModel

class SettingsBackend(BaseBackend):
    def authenticate(self, request, email=None, password=None):
        try:
            user = UserModel.objects.get(email=email)
            if user.check_password(password):
                return user
        except UserModel.DoesNotExist:
            return None  # 인증 실패 시 None 반환

    def get_user(self, user_id):
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None