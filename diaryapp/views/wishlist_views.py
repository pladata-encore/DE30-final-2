import json

from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
import logging
from ..forms import *
from ..models import *
from ..mongo_queries import get_mongodb_connection
from bson.objectid import ObjectId
import json

logger = logging.getLogger(__name__)

'''다이어리 찜 기능'''
# @login_required
# @require_POST
# def add_wish(request):
#     try:
#         plan_id = request.POST.get('plan_id')
#         user_email = 'dobi3@nate.com'  # 실제 환경에서는 로그인한 사용자의 이메일을 사용해야 합니다.
#
#         logger.info(f"Attempting to add wish for plan_id: {plan_id}, user_email: {user_email}")
#
#         if not plan_id:
#             return JsonResponse({'status': 'error', 'message': 'plan_id is required'}, status=400)
#
#         # 중복 체크 (plan_id 기준)
#         existing_wish = Wishlist.objects.filter(user_email=user_email, plan_id=plan_id).first()
#         if existing_wish:
#             logger.info(f"Wish already exists for plan_id: {plan_id}, user_email: {user_email}")
#             return JsonResponse({'status': 'success', 'created': False, 'message': '이미 찜한 계획입니다.'})
#
#         # 새로운 위시리스트 항목 생성
#         new_wish = Wishlist(
#             user_email=user_email,
#             plan_id=plan_id,
#             place=request.POST.get('place'),
#             province=request.POST.get('province'),
#             city=request.POST.get('city'),
#             travel_dates=json.loads(request.POST.get('travel_dates', '[]')),
#         )
#         new_wish.save()
#
#         logger.info(f"Successfully added new wish for plan_id: {plan_id}, user_email: {user_email}")
#         return JsonResponse({'status': 'success', 'created': True, 'message': '성공적으로 찜 목록에 추가되었습니다.'})
#
#     except json.JSONDecodeError:
#         logger.error("Invalid JSON format for travel_dates")
#         return JsonResponse({'status': 'error', 'message': '유효하지 않은 travel_dates 형식'}, status=400)
#
#     except Exception as e:
#         logger.exception(f"Error in add_wish: {str(e)}")
#         logger.error(f"Request data: {request.POST}")
#         return JsonResponse({'status': 'error', 'message': '서버 오류가 발생했습니다.'}, status=500)




@require_POST
def add_wish(request):
    try:
        plan_id = request.POST.get('plan_id')
        # user_email = 'dobi3@nate.com'  # 실제 환경에서는 로그인한 사용자의 이메일을 사용해야 합니다.
        user_email = request.session.get('userSession')
        print(f"-------wish session-------{user_email}")

        logger.info(f"Attempting to add wish for plan_id: {plan_id}, user_email: {user_email}")

        if not plan_id:
            return JsonResponse({'status': 'error', 'message': 'plan_id is required'}, status=400)

        # 중복 체크 (plan_id 기준)
        existing_wish = Wishlist.objects.filter(user_email=user_email, plan_id=plan_id).first()
        if existing_wish:
            logger.info(f"Wish already exists for plan_id: {plan_id}, user_email: {user_email}")
            return JsonResponse({'status': 'success', 'created': False, 'message': '이미 찜한 계획입니다.'})

        # MongoDB 연결 및 plan 데이터 가져오기
        db = get_mongodb_connection()
        plan_collection = db['plan']
        plan = plan_collection.find_one({"plan_id": plan_id})

        if not plan:
            logger.error(f"Plan not found for plan_id: {plan_id}")
            return JsonResponse({'status': 'error', 'message': '해당 계획을 찾을 수 없습니다.'}, status=404)

        # Jplan과 Pplan 구분
        if plan_id.startswith('PK'):  # Pplan
            wish_data = {
                'plan_id': plan_id,
                'province': plan.get('province', ''),
                'city': plan.get('city', ''),
                'days': plan.get('days', {})
            }
        else:  # Jplan
            wish_data = {
                'plan_id': plan_id,
                'province': plan.get('province', ''),
                'city': plan.get('city', ''),
                'days': [
                    {
                        'date': day.get('date', ''),
                        'recommendations': [{'title': rec.get('title', '')} for rec in day.get('recommendations', [])]
                    } for day in plan.get('days', [])
                ]
            }

        # 새로운 위시리스트 항목 생성
        new_wish = Wishlist(
            user_email=user_email,
            plan_id=plan_id,
            place=wish_data['city'],
            province=wish_data['province'],
            city=wish_data['city'],
            travel_dates=wish_data['days']
        )
        new_wish.save()

        logger.info(f"Successfully added new wish for plan_id: {plan_id}, user_email: {user_email}")
        return JsonResponse({'status': 'success', 'created': True, 'message': '성공적으로 찜 목록에 추가되었습니다.'})

    except Exception as e:
        logger.exception(f"Error in add_wish: {str(e)}")
        logger.error(f"Request data: {request.POST}")
        return JsonResponse({'status': 'error', 'message': '서버 오류가 발생했습니다.'}, status=500)

'''일정 찜 리스트'''
# def wishlist_view(request):
#     # user_email = request.user.email
#     user_email = 'dobi3@nate.com'
#     wishlist_items = Wishlist.objects.filter(user_email=user_email).order_by('added_at')
#
#     paginator = Paginator(wishlist_items, 10)
#     page_number = request.GET.get('page')
#
#     try:
#         page_obj = paginator.page(page_number)
#     except PageNotAnInteger:
#         page_obj = paginator.page(1)
#     except EmptyPage:
#         page_obj = paginator.page(paginator.num_pages)
#
#     context = {
#         'page_obj': page_obj
#     }
#     return render(request, 'diaryapp/wishlist.html', context)
def wishlist_view(request):
    # user_email = 'dobi3@nate.com'
    user_email = request.session.get('userSession')
    print(f"-------wish session-------{user_email}")
    wishlist_items = Wishlist.objects.filter(user_email=user_email).order_by('-added_at')

    # travel_dates 필드의 내용을 로그로 출력
    for item in wishlist_items:
        print(f"Plan ID: {item.plan_id}, Travel Dates: {item.travel_dates}")

    paginator = Paginator(wishlist_items, 10)
    page_number = request.GET.get('page')

    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    context = {
        'page_obj': page_obj
    }
    return render(request, 'diaryapp/wishlist.html', context)

'''일정 삭제'''
def remove_wish(request, plan_id):
    # user_email = 'dobi3@nate.com'  # 로그인된 사용자의 이메일 가져오기
    user_email = request.session.get('userSession')
    print(f"-------wish session-------{user_email}")
    try:
        wishlist_item = Wishlist.objects.get(user_email=user_email, plan_id=plan_id)
        wishlist_item.delete()
        return redirect('wishlist_view')
    except Wishlist.DoesNotExist:
        return HttpResponseForbidden("이 항목을 삭제할 권한이 없습니다.")