import os
import openai
from django.contrib.auth.decorators import login_required
from dotenv import load_dotenv
import gridfs
import torch
import open_clip
from PIL import Image
from django.http import HttpResponse
from django.utils import timezone
from pymongo import MongoClient
from transformers import GPT2LMHeadModel, GPT2Tokenizer
from django.shortcuts import render, get_object_or_404, redirect
from myproject import settings
from ..forms import *
from ..models import *
from googletrans import Translator
import base64

from django.forms.models import modelformset_factory
from django.contrib.auth.models import User


'''뱃지 아이디 가져오기-해당유저를 찾은 후 유저가 매핑되어 있는 뱃지를 찾는다'''
# def get_user_badge_id(user):
#     # 사용자의 프로필 정보를 가져오는 예시 코드
#     try:
#         # 사용자 모델에 profile 필드가 있다고 가정
#         profile = user.profile  # 사용자의 프로필 정보 가져오기
#         badge_id = profile.badge_id  # 프로필에서 뱃지 ID 가져오기
#     except AttributeError:
#         # 프로필 정보나 뱃지 ID가 없는 경우에 대한 에러 처리
#         badge_id = None  # 또는 기본값 설정 등
#     return badge_id


'''댓글 생성'''
# @login_required
def create_comment(request, unique_diary_id):
    diary = get_object_or_404(AiwriteModel, unique_diary_id=unique_diary_id)

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user_email = request.user.email  # 로그인한 사용자의 이메일로 설정 - 계정이 요상하게 들어감
            comment.save()
            comment.diary_id.set([diary])  # ManyToMany 관계 설정
            return redirect('detail_diary_by_id', unique_diary_id=unique_diary_id)

    return render(request, 'diaryapp/detail_diary.html', {'diary': diary, 'form': form})

'''해당 다이어리에 달린 댓글들 리스트 확인
    CommentModel 컬렉션에서 해당 다이어리의 unique_diary_id가 저장되어있는 데이터들을 모두 반환'''
def list_comment(request,unique_diary_id):
    # user_email = request.user.email if request.user.is_authenticated else None
    user_email = settings.DEFAULT_FROM_EMAIL
    diary = get_object_or_404(AiwriteModel, unique_diary_id=unique_diary_id)
    comment_list = CommentModel.objects.all().order_by('-created_at')
    return render(request, 'diaryapp/detail_diary_by_id.html', {'comment_list': comment_list})

''' 댓글 삭제하기
    # 로그인된 사용자와 해당 댓글 작성자가 일치할 경우에만 삭제버튼 활성화 '''
# @login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(CommentModel, comment_id=comment_id)
    if comment.user_email == request.user.email:  # 작성자만 삭제할 수 있도록
        comment.delete()
    return redirect('detail_diary', unique_diary_id=comment.diary_id.first().unique_diary_id)
