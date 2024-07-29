from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST

from ..forms import *
from ..models import *

'''다이어리 찜 기능'''
# @login_required
@require_POST
def add_wish(request):
    place = request.POST.get('place')
    user_email = settings.DEFAULT_FROM_EMAIL  # 사용자 이메일 가져오기 (로그인된 경우)

    if not user_email:
        return JsonResponse({'status': 'error', 'message': '로그인 필요'}, status=403)

    try:
        exists = Wishlist.objects.filter(user_email=user_email, place=place).exists()
        if exists:
            return JsonResponse({'status': 'success', 'created': False})

        Wishlist.objects.create(user_email=user_email, place=place)
        return JsonResponse({'status': 'success', 'created': True})
    except Exception as e:
        # 로그 기록이나 추가적인 에러 처리가 필요할 수 있습니다.
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


'''일정 찜 리스트'''
def wishlist_view(request):
    user_email = settings.DEFAULT_FROM_EMAIL
    wishlist_items = Wishlist.objects.filter(user_email=user_email).order_by('added_at')  # 정렬 추가

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

    user_email = settings.DEFAULT_FROM_EMAIL
    try:
        wishlist_item = Wishlist.objects.get(user_email=user_email, place=place)
        wishlist_item.delete()
        return redirect('wishlist_view')
    except Wishlist.DoesNotExist:
        return HttpResponseForbidden("이 항목을 삭제할 권한이 없습니다.")