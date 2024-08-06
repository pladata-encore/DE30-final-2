import json

from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
import logging
from ..forms import *
from ..models import *

logger = logging.getLogger(__name__)

'''다이어리 찜 기능'''
# @login_required
@require_POST
def add_wish(request):
    try:
        place = request.POST.get('place')
        province = request.POST.get('province')
        city = request.POST.get('city')
        travel_dates = request.POST.get('travel_dates')
        user_email = 'dobi3@nate.com'
        # user_email = request.user.email  # 로그인된 사용자의 이메일 가져오기

        if not user_email:
            return JsonResponse({'status': 'error', 'message': '로그인 필요'}, status=403)

        logger.debug(f"Place: {place}, Province: {province}, City: {city}, Travel Dates: {travel_dates}")

        exists = Wishlist.objects.filter(user_email=user_email, place=place, province=province, city=city).exists()
        if exists:
            return JsonResponse({'status': 'success', 'created': False})

        Wishlist.objects.create(user_email=user_email, place=place, province=province, city=city,
                                travel_dates=json.loads(travel_dates))
        return JsonResponse({'status': 'success', 'created': True})

    except Exception as e:
        logger.error(f"Error in add_wish: {e}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)



'''일정 찜 리스트'''
def wishlist_view(request):
    user_email = 'dobi3@nate.com'
    wishlist_items = Wishlist.objects.filter(user_email=user_email).order_by('added_at')

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
def remove_wish(request, place):
    # if not request.user.is_authenticated:
    #     return redirect('login')  # 로그인 필요시

    user_email = 'dobi3@nate.com'  # 로그인된 사용자의 이메일 가져오기
    try:
        wishlist_item = Wishlist.objects.get(user_email=user_email, place=place)
        wishlist_item.delete()
        return redirect('wishlist_view')
    except Wishlist.DoesNotExist:
        return HttpResponseForbidden("이 항목을 삭제할 권한이 없습니다.")