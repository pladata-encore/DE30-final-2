import requests
import random
import string
from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
import logging
import pymongo
import urllib.parse

logger = logging.getLogger(__name__)

# MongoDB URI 생성
username = 'Seora'
password = 'playdata6292'
encoded_username = urllib.parse.quote_plus(username)
encoded_password = urllib.parse.quote_plus(password)
mongo_uri = f"mongodb+srv://{encoded_username}:{encoded_password}@mydiary.727yxhm.mongodb.net/MyDiary?retryWrites=true&w=majority"

# MongoDB 클라이언트 생성
client = pymongo.MongoClient(mongo_uri)
db = client['MyDiary']
collection = db['users_usermodel']

# 네이버 로그인 및 프로필 URL
naver_login_url = "https://nid.naver.com/oauth2.0/authorize"
naver_token_url = "https://nid.naver.com/oauth2.0/token"
naver_profile_url = "https://openapi.naver.com/v1/nid/me"

class NaverLoginView(APIView):
    permission_classes = [AllowAny]

    def generate_state(self):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=16))

    def get(self, request):
        print('************* 1')
        '''
        naver code 요청
        '''
        client_id = settings.NAVER_CLIENT_ID
        redirect_uri = settings.NAVER_REDIRECT_URI
        state = self.generate_state()
        uri = f"{naver_login_url}?client_id={client_id}&redirect_uri={redirect_uri}&state={state}&response_type=code"
        print(uri)
        return redirect(uri)

class NaverCallbackView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        print('************* 2')
        '''
        네이버에서 액세스 토큰 및 사용자 정보 요청
        ---
        '''
        code = request.GET.get('code')
        user_state = request.GET.get('state')

        if not code or not user_state:
            return Response({'error': 'Missing code or state'}, status=status.HTTP_400_BAD_REQUEST)

        # 액세스 토큰 요청
        request_data = {
            'grant_type': 'authorization_code',
            'client_id': settings.NAVER_CLIENT_ID,
            'redirect_uri': settings.NAVER_REDIRECT_URI,
            'client_secret': settings.NAVER_CLIENT_SECRET,
            'code': code,
            'state': user_state,
        }
        token_response = requests.post(naver_token_url, data=request_data)

        if token_response.status_code != 200:
            return Response({'error': 'Failed to obtain access token'}, status=status.HTTP_400_BAD_REQUEST)

        token_json = token_response.json()
        access_token = token_json.get('access_token')
        print('naver access token: ', access_token)

        if not access_token:
            return Response({'error': 'Access token not found'}, status=status.HTTP_400_BAD_REQUEST)

        # 사용자 프로필 정보 요청
        headers = {"Authorization": f"Bearer {access_token}"}
        profile_response = requests.get(naver_profile_url, headers=headers)

        if profile_response.status_code != 200:
            return Response({'error': 'Failed to get user profile'}, status=status.HTTP_400_BAD_REQUEST)

        profile_data = profile_response.json()
        user_info = profile_data.get('response', {})
        email = user_info.get('email')

        if not email:
            return Response({'error': 'Email not found'}, status=status.HTTP_400_BAD_REQUEST)

        # MongoDB에서 사용자 정보 조회
        existing_user = collection.find_one({'email': email})

        User = get_user_model()

        try:
            if existing_user:
                # MongoDB에서 사용자 데이터 가져오기
                mongo_user_data = {
                    'username': existing_user.get('username'),
                    'gender': existing_user.get('gender'),
                    'nickname': existing_user.get('nickname'),
                    'email': existing_user.get('email'),
                }
                # 여러 사용자 처리
                user_list = User.objects.filter(email=email)
                if user_list.exists():
                    user = user_list.first()
                    for attr, value in mongo_user_data.items():
                        setattr(user, attr, value)
                    user.save()
                else:
                    user = User.objects.create(**mongo_user_data)
                    user.isSocial = 1
                    user.save()
            else:
                user_data = {
                    'username': user_info.get('name'),
                    'gender': user_info.get('gender'),
                    'nickname': user_info.get('nickname'),
                    'email': email
                }
                user = User.objects.create(**user_data)
                user.isSocial = 1
                user.save()

                collection.insert_one({
                    'email': email,
                    'username': user_info.get('name'),
                    'gender': user_info.get('gender'),
                    'nickname': user_info.get('nickname'),
                    'isSocial': 1
                })

            # 사용자 로그인 처리
            # login(request, user, backend='django.contrib.auth.backends.ModelBackend')

            #로그 추가
            print(f"User {user.email} logged in successfully with session key: {request.session.session_key}")
            print(f"Session data: {request.session.items()}")

            return HttpResponseRedirect(reverse('travel:service_main'))

        except Exception as e:
            logger.error(f"An unexpected error occurred: {str(e)}")
            return Response({'error': 'An unexpected error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)