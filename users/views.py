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
from users.serializers import UserInfoSerializer, LoginSerializer, LogoutSerializer, RefreshTokenSerializer
from .forms import UserRegistrationForm,LoginForm
from users.lib.permission import LoginRequired
from django.contrib.auth.hashers import check_password
from django.contrib.auth.hashers import make_password
from django.http import JsonResponse
from django.conf import settings
from .services import authenticate_user
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth import authenticate
from pymongo import MongoClient
from django.contrib.auth import get_user_model
import urllib.parse


# 로깅 설정
logger = logging.getLogger(__name__)

# MongoDB 연결 설정---------아틀라스-------------------


# URL 인코딩할 사용자 이름과 비밀번호
# username = 'Seora'
# password = 'playdata6292'
#
# # URL 인코딩
# encoded_username = urllib.parse.quote_plus(username)
# encoded_password = urllib.parse.quote_plus(password)
#
# # # MongoDB URI 생성
# mongo_uri = f"mongodb+srv://{encoded_username}:{encoded_password}@mydiary.727yxhm.mongodb.net/MyDiary?retryWrites=true&w=majority"
#
# database_name='MyDiary'
# collection_name='users'
#
# # MongoDB 클라이언트 생성
# client = MongoClient(mongo_uri, tls=True, tlsAllowInvalidCertificates=True)
# db = client['MyDiary']
# collection = db['users']

#---------------------------------설아 도커----------------------------------------------------------
#설아 도커 연결
client = MongoClient('mongodb://192.168.0.25:27017/', tls=True, tlsAllowInvalidCertificates=True)

#MongoDB 클라이언트 설정
db = settings.MONGO_CLIENT[settings.DATABASES['default']['NAME']]

# 컬렉션
user_collection = db['users']
user_model_collection = db['users_model']

#-------------------------설아 도커-------------------------------------------------------------------
class User:
    def __init__(self, username, email, password, gender, nickname, mongo_id):
        self.mongo_id = mongo_id
        self.username = username
        self.email = email
        self.password = password
        self.gender = gender
        self.nickname = nickname


#추가
UserModel = get_user_model()

def get_user_from_db(email):
    try:
        user_data = user_collection.find_one({"email": email})
        if user_data:
            # MongoDB에서 가져온 데이터를 Django의 UserModel 인스턴스로 변환
            try:
                user = UserModel.objects.filter(email=email).first()
            except UserModel.DoesNotExist:
                # UserModel에 없을 경우 새로운 UserModel 객체를 생성
                user = UserModel(
                    email=user_data['email'],
                    username=user_data['username'],
                    gender=user_data['gender'],
                    nickname=user_data['nickname'],
                    password=user_data['password']  # 이미 해시된 비밀번호를 사용
                )
                user.save()
            return user
        return None

    except ConnectionError as e:
        print(f"Error connecting to MongoDB: {e}")
        return None


def authenticate_user(email, password):
    print("************ authenticate_user ",email, password)
    user = get_user_from_db(email)
    if user:
        print("사용자 데이터: ", user.email, user.password)  # 사용자 데이터 출력

        # Assuming passwords are hashed; use Django's password checking utility
        if check_password(password, user.password):  # 비밀번호 확인
            print("비밀번호 일치")
            return user
        else:
            print("비밀번호 불일치")
    else:
        print("사용자 없음")
    return None
# end-----------------



class HomeView(TemplateView):
    template_name = 'users/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_session = self.request.session.get('userSession','Anonymous')
        context['userSession'] = user_session
        return context

#------------------------------------------------------------------
# 사용자 등록 함수
def register(request):
    if request.method == 'POST':
        logger.debug("POST 요청이 들어왔습니다.")
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
                # hashed_password = make_password(password1)
                # print("해시된 비밀번호: ", hashed_password)  # 해시된 비밀번호 출력
                user = user_model.objects.create_user(
                    email=email,
                    username=username,
                    password=password1,
                    gender=gender,
                    nickname=nickname
                )

                # MongoDB에 데이터 삽입할 데이터
                data = {
                    'email': email,
                    'username': username,
                    'gender': gender,
                    'password': user.password,
                    'nickname': nickname,
                    'register_id': None
                }
                print(f"Data to insert: {data}")


                try:
                    result = user_collection.insert_one(data)
                    # result = users_collection.insert_one(data)
                    user.register_id = str(result.inserted_id)
                    user.save()

                    # 저장된 비밀번호 해시 값 확인
                    mongo_stored_password = user_collection.find_one({"email": email})["password"]
                    django_stored_password = user.password

                    print("MongoDB에 저장된 비밀번호 해시 값: ", mongo_stored_password)
                    print("Django UserModel에 저장된 비밀번호 해시 값: ", django_stored_password)

                    if mongo_stored_password == django_stored_password:
                        print("비밀번호 해시 값이 일치합니다.")
                    else:
                        print("비밀번호 해시 값이 일치하지 않습니다.")


                    return redirect('users:home')
                except Exception as e:
                    user.delete()
                    messages.error(request, "MongoDB 데이터 삽입 실패")
                    return redirect('users:register')


                #인증 및 로그인
                # user = authenticate(request, email=email, password=password1)
                # if user is not None:
                #     login(request, user)
                # return redirect('users:home')

            except Exception as e:
                messages.error(request, f"회원가입 중 오류 발생: {e}")
                return redirect('users:register')

    else:
        form = UserRegistrationForm()
        return render(request, 'users/register.html', {'form': form})
    #     return render(request,  'users/register.html')
    # 가야할 곳은 아래
    # return HttpResponseRedirect(reverse('users:register'))


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
        print("POST 요청이 들어왔습니다.")
        form = LoginForm(request.POST)
        if form.is_valid():
            print("폼이 유효합니다.")
            email = form.cleaned_data['email']  # email
            password = form.cleaned_data['password']
            print(f"email: {email}, password: {password}")
            user = authenticate_user(email, password)
            print(f"인증된 사용자: {user}")

            if user is not None and isinstance(user, UserModel):
                print("로그인 성공, 사용자 정보를 세션에 저장합니다.")
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                login(request, user)
                request.session['userSession'] = user.email
                print(f"-------------------------------------login_view---------------------{request.session['userSession']}")

                response_data = {
                    'status': 'success',
                    'redirect': 'http://localhost:8000/travel/'
                }
                return JsonResponse(response_data)
            else:
                print("로그인 실패, 유효하지 않은 사용자이거나 인증 실패.")
                errors = form.errors.as_json()
                response_data = {
                    'status': 'error',
                    'message': '아이디 혹은 비밀번호가 올바르지 않습니다',
                    'errors': form.errors
                }
                return JsonResponse(response_data, status=400)
        else:
            print("폼 유효성 검사 실패:", form.errors)
            response_data = {
                'status': 'error',
                'message': '유효성 검사에 실패했습니다',
                'errors': form.errors.as_json()
            }
            return JsonResponse(response_data, status=400)
    else:
        print("GET 요청이 들어왔습니다.")
        form = LoginForm()
        return render(request, 'users/login.html', {'form': form})






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