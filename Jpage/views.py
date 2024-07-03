from django.shortcuts import render
from django.http import JsonResponse
from pymongo import MongoClient
from .models import categoryCode1, categoryCode2, categoryCode3


client = MongoClient('mongodb+srv://Seora:youlove4154@mydiary.727yxhm.mongodb.net/MyDiary?retryWrites=true&w=majority', 27017)
db = client.MyDiary

def get_category(request):
    # 모든 대분류 데이터를 가져옴
    largecategories = categoryCode1.objects.all()

    # 선택된 대분류의 코드 가져오기 (예: GET 파라미터를 통해 전달됨)
    selected_cat1_code = request.GET.get('cat1_code')

    # 선택된 대분류 코드와 일치하는 중분류 데이터만 가져옴
    if selected_cat1_code:
        middlecategories = categoryCode2.objects.filter(cat1_code=selected_cat1_code).values('_id', 'name')
    else:
        middlecategories = categoryCode2.objects.none()  # 아무 것도 선택되지 않은 경우 빈 쿼리셋

    # 컨텍스트에 대분류와 중분류 데이터를 추가
    context = {
        'largecategories': largecategories,
        'middlecategories': middlecategories
    }

    # 템플릿 렌더링
    return render(request, 'Jpage/map.html', context)