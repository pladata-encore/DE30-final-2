import os
import openai
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
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
from .badge_views import get_main_badge
from ..forms import *
from ..models import *
from googletrans import Translator
import base64

from django.forms.models import modelformset_factory
from django.contrib.auth.models import User

'''댓글 생성'''
# @login_required
def create_comment(request, unique_diary_id):
    diary = get_object_or_404(AiwriteModel, unique_diary_id=unique_diary_id)

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            # comment.user_email = request.user.email  # 로그인한 사용자의 이메일로 설정 - 계정이 요상하게 들어감
            comment.user_email = settings.DEFAULT_FROM_EMAIL  # 로그인한 사용자의 이메일로 설정 - 계정이 요상하게 들어감
            comment.save()
            comment.diary_id.set([diary])  # ManyToMany 관계 설정
            return redirect('detail_diary_by_id', unique_diary_id=unique_diary_id)
        else:
            form = CommentForm()
    return render(request, 'diaryapp/detail_diary.html', {'diary': diary, 'form': form})

'''해당 다이어리에 달린 댓글들 리스트 확인
    CommentModel 컬렉션에서 해당 다이어리의 unique_diary_id가 저장되어있는 데이터들을 모두 반환'''
def list_comment(request, unique_diary_id):
    diary = get_object_or_404(AiwriteModel, unique_diary_id=unique_diary_id)
    comment_list = CommentModel.objects.filter(diary_id=diary).order_by('-created_at')

    # 각 댓글에 대한 뱃지 정보 가져오기
    for comment in comment_list:
        _, nickname, badge_name, badge_image = get_main_badge(comment.user_email)
        comment.nickname = nickname
        comment.badge_name = badge_name
        comment.badge_image = badge_image

    return render(request, 'diaryapp/detail_diary.html', {'comment_list': comment_list})
''' 댓글 삭제하기
    # 로그인된 사용자와 해당 댓글 작성자가 일치할 경우에만 삭제버튼 활성화 '''
# @login_required
def delete_comment(request, diary_id, comment_id):
    comment = get_object_or_404(CommentModel, comment_id=comment_id)
    # if comment.user_email != request.user.email:
    if comment.user_email != settings.DEFAULT_FROM_EMAIL:
        raise PermissionDenied("You do not have permission to delete this comment.")
    comment.delete()
    return redirect('detail_diary_by_id', unique_diary_id=diary_id)