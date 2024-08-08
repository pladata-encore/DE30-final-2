import logging
from pymongo import MongoClient
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.views.generic import TemplateView
from .serializers import UserInfoSerializer, LoginSerializer, LogoutSerializer, RefreshTokenSerializer
from .forms import UserRegistrationForm,LoginForm
from users.lib.permission import LoginRequired
from django.contrib.auth.hashers import check_password
from django.contrib.auth.hashers import make_password
from django.http import JsonResponse

# 로깅 설정
logger = logging.getLogger(__name__)

# MongoDB 연결 설정
import urllib.parse
from pymongo import MongoClient

# URL 인코딩할 사용자 이름과 비밀번호
username = 'Seora'
password = 'playdata6292'

# URL 인코딩
encoded_username = urllib.parse.quote_plus(username)
encoded_password = urllib.parse.quote_plus(password)

# # MongoDB URI 생성
# mongo_uri = f"mongodb+srv://{encoded_username}:{encoded_password}@mydiary.727yxhm.mongodb.net/MyDiary?retryWrites=true&w=majority"

# 설아 도커 연결
client = MongoClient('mongodb://127.0.0.1:27017/', tls=True, tlsAllowInvalidCertificates=True)

db = client['MyDiary']
collection = db['users']

# start-------------
class User:
    def __init__(self, id, username, email, password, gender, nickname, mongo_id):
        self.id = id
        self.username = username
        self.email = email
        self.password = password
        self.gender = gender
        self.nickname = nickname
        self.mongo_id = mongo_id


def get_user_from_db(email):
    try:
        # Connect to MongoDB
        db = client['MyDiary']
        collection = db['users']

        # Find user by username
        user_data = collection.find_one({"email": email})
        if user_data:
            return User(
                id=user_data.get('_id'),
                username=user_data.get('username'),
                email=user_data.get('email'),
                password=user_data.get('password'),
                gender=user_data.get('gender'),
                nickname=user_data.get('nickname'),
                mongo_id=user_data.get('mongo_id')
            )
        return None

    except ConnectionError as e:
        print(f"Error connecting to MongoDB: {e}")
        return None


def authenticate_user(email, password):
    user = get_user_from_db(email)
    if user:
        # Assuming passwords are hashed; use Django's password checking utility
        if user and check_password(password, user.password):  # 비밀번호 확인
            return user
    return None
# end-----------------



class HomeView(TemplateView):
    template_name = 'users/home.html'


# 사용자 등록 함수
def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password1 = form.cleaned_data['password1']
            password2 = form.cleaned_data['password2']
            gender = form.cleaned_data['gender']
            nickname = form.cleaned_data['nickname']

            # 비밀번호 확인
            if password1 != password2:
                messages.error(request, "비밀번호가 일치하지 않습니다.")
                return redirect('users:register')

            try:
                # 사용자 생성
                user_model = get_user_model()
                hashed_password = make_password(password1)
                user = user_model.objects.create_user(
                    email=email,
                    username=username,
                    password=hashed_password,
                    gender=gender,
                    nickname=nickname
                )

                # MongoDB에 데이터 삽입할 데이터
                data = {
                    'email': email,
                    'username': username,
                    'gender': gender,
                    'password': hashed_password,
                    'nickname': nickname,
                    'register_id': user.register_id
                }
                print(f"Data to insert: {data}")
                result = None
                try:
                    user.register_id = str(result.inserted_id)
                    result = collection.insert_one(data)
                    user.save()
                except Exception as e:
                    user.delete()
                    messages.error(request, "MongoDB 데이터 삽입 실패")
                    return redirect('users:register')

                #인증 및 로그인
                user = authenticate(request, email=email, password=password1)
                if user is not None:
                    login(request, user)
                return redirect('users:home')

            except Exception as e:
                messages.error(request, f"회원가입 중 오류 발생: {e}")
                return redirect('users:register')

    else:
        form = UserRegistrationForm()
    return render(request, 'users/register.html', {'form': form})


def logout_view(request):
    # 현재 사용자의 세션을 종료
    print("******************** logout_view")
    logout(request)

    # 클라이언트에 JSON 응답을 반환
    response_data = {
        'status': 'success',
        'redirect': '/users/home'  # 로그아웃 후 리다이렉트할 URL
    }
    return JsonResponse(response_data)

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']  # email
            password = form.cleaned_data['password']
            user = authenticate_user(username,password)

            if user is not None:
                # 로그인 성공
                response_data = {
                    'status': 'success',
                    'redirect': '/users/home'  # 성공 시 리다이렉트할 URL
                }
                return JsonResponse(response_data)
            else:
                # 로그인 실패
                response_data = {
                    'status': 'error',
                    'message': '아이디 혹은 비밀번호가 올바르지 않습니다'
                }
                return JsonResponse(response_data, status=400)

    else:
        form = LoginForm()
    return render(request, 'users/login.html', {'form':form})






# 사용자 뷰
class UserView(APIView):
    permission_classes = [AllowAny]

    def get_or_create_user(self, data: dict):
        serializer = CreateUserSerializer(data=data)

        if not serializer.is_valid():
            logger.error('User creation failed due to invalid data')
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save()
        logger.info('User created successfully')
        return Response(data=user, status=status.HTTP_201_CREATED)
        # serializer.create(validata=user)
        #
        # return Response(data=user, status=status.HTTP_201_CREATED)

    def post(self, request):
        '''
        계정 조회 및 등록
        '''
        logger.info('Received request for user creation')
        return self.get_or_create_user(data=request.data)



# 로그아웃 뷰
class LogoutView(APIView):
    permission_classes = [LoginRequired]
    authentication_classes = [JWTAuthentication]

    @swagger_auto_schema(request_body=LogoutSerializer)
    def post(self, request):
        '''
        로그아웃
        '''
        serializer = LogoutSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.validated_data.blacklist()
        logout(request)

        messages.success(request, '로그아웃이 성공적으로 처리되었습니다')
        return redirect('users:home')



# 토큰 재발급 뷰
class TokenRefreshView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(request_body=RefreshTokenSerializer)
    def post(self, request):
        '''
        Access Token 재발급
        '''
        serializer = RefreshTokenSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        token = serializer.validated_data
        return Response(data=token, status=status.HTTP_201_CREATED)