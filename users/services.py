from django.contrib.auth.hashers import check_password

from users.forms import User


def get_user_from_db(email):
    # 데이터베이스에서 사용자 정보를 가져오는 로직
    user = User.objects.filter(email=email).first()
    if user:
        return user
    return None

def authenticate_user(email, password):
    user = get_user_from_db(email)  # username이 이메일이라고 가정
    if user:
        # 비밀번호 확인 (hashed 비밀번호 확인)
        if check_password(password, user.password):
            return user
    return None