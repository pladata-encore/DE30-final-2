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

from diaryapp.models import AiwriteModel, ImageModel
from .nickname_views import get_nickname
from .badge_views import get_main_badge
from common.context_processors import get_user


# MongoDB 클라이언트 설정
db = settings.MONGO_CLIENT[settings.DATABASES['default']['NAME']]

# 컬렉션
collection = db['areaBaseList']
user_collection = db['users_usermodel']
diary_collection = db['diaryapp_aiwritemodel']
image_collection = db['diaryapp_imagemodel']
plan_collection = db['plan']



logger = logging.getLogger(__name__)

# 다이어리 메인
#@login_required
def viewDiary(request, user_email=None):

    # 사용자 정보 가져오기
    user_info = get_user(request, user_email)
    user = user_info['user']
    is_own_page = user_info['is_own_page']


    # 사용자 다이어리 전체 이름 가져오기
    user['title_diary'] = user.get('title_diary', f"{user.get('username', '즐거운 여행자')}의 여행 다이어리")


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

    # 사용자 다이어리 정보 가져오기
    # user_diaries = AiwriteModel.objects.filter(user_email=user['email'])
    user_diaries = diary_collection.find({'user_email': user['email']})

    try:
        #diaries = user_diaries.order_by('-created_at')[:5]
        diaries = user_diaries.sort('created_at', -1).limit(5)

        for diary in diaries:

            try:

                #if diary.nickname_id == '<JsonResponse status_code=500, "application/json">':
                if diary.get('nickname_id') == '<JsonResponse status_code=500, "application/json">':
                    nickname_id, nickname, badge_name, badge_image = '', '별명이 없습니다.', '', ''
                else:
                    #nickname_id, nickname, badge_name, badge_image = get_nickname(diary.nickname_id)
                    nickname_id, nickname, badge_name, badge_image = get_nickname(diary.get('nickname_id'))

                representative_image = diary.get('encoded_representative_image')

                enriched_diary = {
                    'diary': diary,
                    'representative_image': representative_image,
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
                    'representative_image': None,
                    'nickname': 'Unknown',
                    'badge_name': 'Unknown',
                    'badge_image': 'Unknown',
                })

    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
        logger.error(traceback.format_exc())
        return HttpResponseServerError("An error occurred while accessing the database.")


    # 다이어리 생성 링크
    schedule_links_and_diary_links = []
    try:
        # 다이어리에서 plan_id 추출
        user_diaries = AiwriteModel.objects.filter(user_email=user['email'])
        plan_id_diaries = [diary.plan_id for diary in user_diaries if diary.plan_id]
        print(f'---------------plan_id_diaries-----------{plan_id_diaries}')

        # 계획에서 조건에 맞는 plan_id 필터링
        target_plans = plan_collection.find({
            'email': user['email'],
            'plan_id': {'$nin': plan_id_diaries}
        })

        target_plans_list = list(target_plans)
        target_plans_list.reverse()

        if target_plans_list:
            for plan in target_plans_list:
                plan_id = plan.get('plan_id', '')
                plan_title = plan.get('plan_title', '')

                # 일정에서 title 추출
                valid_titles = []

                if plan_id.startswith('PK'):
                    # 계획_직접 생성
                    days = plan.get('days', {})
                    print(f'---------------J_plan_title-----------{plan_title}')

                    valid_titles.extend(
                        title for titles in days.values() for title in titles
                        if (doc := collection.find_one({'title': title})) and doc['firstimage'].strip() !=""
                    )
                else :
                    # 계획_자동 생성
                    days = plan.get('days', [])
                    print(f'---------------P_plan_title-----------{plan_title}')

                    for day in days:
                        for recommendation in day.get('recommendations', []):
                            title = recommendation.get('title')
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
                    # 각 일정의 url을 추가, 예시로 list_badge, html에는 #
                })
                create_diary_url = reverse('write_diary_plan_id', kwargs={
                    'plan_id': plan_id
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
                title = f"{user.get('username', '즐거운 여행자')}의 여행 다이어리"

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