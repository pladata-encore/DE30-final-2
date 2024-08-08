import datetime as dt
import jwt

from django.contrib.auth import authenticate
from django.conf import settings
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import UserModel, UserRoleModel
from django.contrib.auth import get_user_model


User = get_user_model()


class LoginSerializer(serializers.Serializer):
    email = serializers.CharField(max_length=100)
    token = serializers.CharField(max_length=256, read_only=True)

    def validate(self, data):
        email = data.get('email')
        try:
            user = UserModel.objects.get(email=email)
        except UserModel.DoesNotExist:
            raise serializers.ValidationError({'error': 'User with given email does not exist'})
        # user = authenticate(social_id=data.get('social_id'))
        # if user is None:
        #     raise serializers.ValidationError({'error': 'User with given social_id does not exist'})

        try:
            token = RefreshToken.for_user(user=user)
        except Exception as e:
            raise serializers.ValidationError({'error': f'Failed create Token : {str(e)}'})

        # 사용자 email 변경된 경우 해당 email로 갱신
        if user.email != data['email']:
            user.email = data['email']

        # 최근 로그인시간 갱신
        user.last_login = dt.datetime.now()
        user.save()

        data = {
            'email': user.email,
            'access_token': f'Bearer {str(token.access_token)}',
            'refresh_token': str(token),
        }
        return data


class LogoutSerializer(serializers.Serializer):
    refresh_token = serializers.CharField(max_length=512)

    def validate(self, data):
        try:
            refresh_token = RefreshToken(data['refresh_token'])
        except:
            raise serializers.ValidationError({'error': 'Invalid Token'})

        return refresh_token


class RefreshTokenSerializer(serializers.Serializer):
    refresh_token = serializers.CharField(max_length=512)

    def validate(self, data):
        refresh_token = data['refresh_token']
        try:
            token = jwt.decode(data['refresh_token'], key=settings.SECRET_KEY, algorithms=settings.SIMPLE_JWT['ALGORITHM'])
        except jwt.ExpiredSignatureError:
            raise serializers.ValidationError({'error': 'Token Signature has expired'})
        except jwt.InvalidTokenError:
            raise serializers.ValidationError({'error': 'Invalid Token'})

        email = token.get('email')
        if not email:
            raise serializers.ValidationError({'error': 'No email found in token'})

        try:
            user = UserModel.objects.get(email=email)
        except UserModel.DoesNotExist:
            raise serializers.ValidationError({'error': 'Invalid User'})

        #Validate the refresh token
        try:
            refresh_token_obj = RefreshToken(refresh_token)
        except Exception as e:
            raise serializers.ValidationError({'error': f'Invalid Token: {str(e)}'})

        data = {
            'access_token': f'Beare {str(refresh_token_obj.access_token)}',
            'refresh_token': str(refresh_token_obj),
        }
        return data


        # try:
        #     _ = UserModel.objects.get(social_id=token['social_id'])
        # except UserModel.DoesNotExist:
        #     raise serializers.ValidationError({'error': 'Invalid User'})
        #
        # try:
        #     refresh_token = RefreshToken(data['refresh_token'])
        # except:
        #     raise serializers.ValidationError({'error': 'Invalid Token'})
        #
        # data = {
        #     'access_token': f'Bearer {str(refresh_token.access_token)}',
        #     'refresh_token': str(refresh_token),
        # }
        # return data


class UserInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserModel
        fields = ('email', 'username', 'gender', 'nickname', 'register_id')
        read_only_fields = ('email', 'mongo_id')

        # read_only_fields = ('social_id', 'social_type', 'email', 'created_at', 'last_login')


class UserInfoPhoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserModel
        fields = ('email', 'username', 'gender', 'nickname', 'register_id')