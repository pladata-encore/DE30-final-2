import logging
import traceback

from django.contrib.auth.decorators import login_required
from django.db import DatabaseError
from django.http import HttpResponseServerError
from django.shortcuts import render, get_object_or_404
from diaryapp.models import AiwriteModel
from diaryapp.views.nickname_views import get_nickname
from myproject import settings

logger = logging.getLogger(__name__)

# @login_required

def viewDiary(request, user_email=None):
    if user_email is None:
        user_email = request.user.email
    else:
        # User = get_user_model()
        # user = get_object_or_404(User, email=user_email)
        # user_email = user.email
        user_email = settings.DEFAULT_FROM_EMAIL

    enriched_diary_list = []

    try:
        diaries = AiwriteModel.objects.filter(user_email=user_email).order_by('-created_at')[:5]

        logger.info(f"Retrieved diaries for {user_email}")
        for diary in diaries:
            logger.info(f"Diary: {diary.unique_diary_id}, Title: {diary.diarytitle}, Created at: {diary.created_at}")

            try:
                diary_model = get_object_or_404(AiwriteModel, unique_diary_id=diary.unique_diary_id)
                nickname, badge_name, badge_image = get_nickname(diary_model.nickname_id)
                enriched_diary = {
                    'diary': diary,
                    'nickname': nickname,
                    'badge_name': badge_name,
                    'badge_image': badge_image
                }
                enriched_diary_list.append(enriched_diary)
            except Exception as e:
                logger.error(f"Error retrieving additional info for diary {diary.unique_diary_id}: {str(e)}")
                logger.error(traceback.format_exc())
                enriched_diary_list.append({
                    'diary': diary,
                    'nickname': 'Unknown',
                    'badge_name': 'Unknown',
                    'badge_image': 'Unknown'
                })

    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
        logger.error(traceback.format_exc())
        return HttpResponseServerError("An error occurred while accessing the database.")

    context = {
        'diary_list': enriched_diary_list,
        'user_email': user_email,
    }
    return render(request, 'diaryapp/diary.html', context)