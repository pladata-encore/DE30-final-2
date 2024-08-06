from django.shortcuts import render, get_object_or_404
import logging
import random
import traceback
from django.db import DatabaseError
from django.http import HttpResponseServerError
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import JsonResponse
from django.urls import reverse

from diaryapp.models import AiwriteModel
from .nickname_views import get_nickname
from .badge_views import get_main_badge
from common.context_processors import get_user

logger = logging.getLogger(__name__)

# 다이어리 메인
#@login_required
def viewDiary(request, user_email=None):

    # 사용자 정보 가져오기
    user_info = get_user(request, user_email)
    user = user_info['user']
    is_own_page = user_info['is_own_page']

    # 사용자 다이어리 전체 이름 가져오기
    user['title_diary'] = user.get('title_diary', f"{user.get('name', '즐거운 여행자')}의 여행 다이어리")

    # 사용자 메인 뱃지 가져오기
    main_nickname_id, main_nickname, main_badge_name, main_badge_image = get_main_badge(user['email'])
    # 사용자 메인 뱃지 링크 생성
    if is_own_page:
        badge_link = reverse('list_badge')
    else:
        diary = diary_collection.find_one({'nickname_id': main_nickname_id})
        if diary :
            unique_diary_id = diary.get('unique_diary_id','')
            badge_link = reverse('detail_diary_by_id', kwargs={'unique_diary_id': unique_diary_id})
        else :
            badge_link = "#"

    # 사용자 다이어리 슬라이드
    enriched_diary_list = []

    try:
        diaries = AiwriteModel.objects.filter(user_email=user['email']).order_by('-created_at')[:5]

        # 디버깅을 위한 로그 추가
        logger.info(f"Retrieved diaries for {user_email}")
        print()
        for diary in diaries:
            logger.info(f"Diary: {diary.unique_diary_id}, Title: {diary.diarytitle}, Created at: {diary.created_at}")

            try:
                diary_model = get_object_or_404(AiwriteModel, unique_diary_id=diary.unique_diary_id)
                nickname_id, nickname, badge_name, badge_image = get_nickname(diary_model.nickname_id)
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


    # 다이어리 생성 링크
    schedule_links_and_diary_links = []
    try:
        # 다이어리에서 plan_id 추출
        # diaries = diary_collection.find({'email': user['email']})
        # plan_id_diaries = [diary['plan_id'] for diary in diaries if 'plan_id' in diary]
        #
        # # 계획에서 조건에 맞는 plan_id 필터링
        # target_plans = plan_collection.find({
        #     'email': user['email'],
        #     'plan_id': {'$nin': plan_id_diaries}
        # })

        # 예시 계획
        target_plans = [{
            'province': '경기도',
            'city': '안산시',
            'email': settings.DEFAULT_FROM_EMAIL,
            'plan_id': 'plan_id입니다.generate_diary 뷰함수가 받아요.',
            'plan_title': '일정 제목 예시입니다. 여기를 누르면 해당 일정으로 이동합니다. 지금은 임시로 나의 여행 뱃지로 이동합니다.',
            'days':{
                "day1": [
                    "가경목장",
                    "귀인한우촌",
                    "김제한우"
                ],
                "day2": [
                    "까망조개이야기",
                    "귀인한우촌",
                    "궁중삼계탕"
                ],
                "day3": [
                    "안산신길온천역휴먼빌2차아파트",
                    "배터지는집",
                    "벚나무집"
                ]
            },
            # 다른 항목은 생략..
        }]

        if target_plans:
            for plan in target_plans:
                plan_id = plan.get('plan_id', '')
                plan_title = plan.get('plan_title', '')
                province = plan.get('province', '')
                city = plan.get('city', '')
                days = plan.get('days', {})

                # 랜덤으로 타이틀 추출
                all_titles = []
                valid_titles = []

                for day, titles in days.items():
                    all_titles.extend(titles)

                for title in all_titles:
                    doc = collection.find_one({'title': title})
                    if doc and doc['firstimage'].strip() != '':
                        valid_titles.append(title)

                if valid_titles:
                    random_title = random.choice(valid_titles)
                    doc = collection.find_one({'title': random_title})
                    bg = doc.get('firstimage','')
                else :
                    random_title = None
                    bg = ''

                # url 생성
                schedule_url = reverse('list_badge',kwargs={
                    #'plan_id': plan_id,
                    # 각 일정의 url을 추가, 예시로 list_badge로 간다
                })
                create_diary_url = reverse('generate_diary_plan_id', kwargs={
                    'plan_id': plan_id,
                    # 'plan_title': plan_title,
                    # 'province': province,
                    # 'city': city,
                })

                schedule_links_and_diary_links.append({
                    'schedule_url': schedule_url,
                    'create_diary_url': create_diary_url,
                    'plan_title': plan_title,
                    'title':random_title,
                    'bg':bg,
                })

    except Exception as e:
        logger.error(f"Error retrieving target plans: {str(e)}")


    context = {
        'user_nickname': main_nickname,
        'user_badge_name': main_badge_name,
        'user_badge_image': main_badge_image,
        'user': user,
        'is_own_page': is_own_page,
        'diary_list': enriched_diary_list,
        'user_email': user_email,
        'schedule_links_and_diary_links': schedule_links_and_diary_links,
        'badge_link': badge_link,
    }

    return render(request, 'diaryapp/diary.html', context)



# 다이어리 제목 설정
# @login_required
def save_title_diary(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        # user_email = request.user.email
        # 로그인 사용자 예시 이메일
        user_email = settings.DEFAULT_FROM_EMAIL

        try:
            user = user_collection.find_one({'email': user_email})
            current_title = user.get('title_diary', '')

            if title == current_title:
                return JsonResponse({'success': True})

            if not title:
                title = f"{user.get('name', '즐거운 여행자')}의 여행 다이어리"

            result = user_collection.update_one(
                {'email': user_email},
                {'$set': {'title_diary': title}}
            )

            if result.matched_count > 0:
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'message': '사용자를 찾을 수 없습니다.'})

        except Exception as e:
            return JsonResponse({'success': False, 'message': '서버 오류: ' + str(e)})

    return JsonResponse({'success': False, 'message': '잘못된 요청입니다.'})