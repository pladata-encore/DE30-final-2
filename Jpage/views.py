from django.shortcuts import render
from django.http import JsonResponse
from pymongo import MongoClient
from .models import categoryCode1, categoryCode2, categoryCode3, areaCode, cityDistrict, areaBaseList, jPlan
from common.context_processors import get_user
from django.views.decorators.csrf import csrf_exempt
import json
from django.shortcuts import render
from django.http import HttpRequest



# client = MongoClient('mongodb+srv://Seora:playdata6292@mydiary.727yxhm.mongodb.net/MyDiary?retryWrites=true&w=majority', 27017)
# db = client.MyDiary
client = MongoClient('mongodb://localhost:27017/',
                     27017)
db = client.MyDiary

def jpagerender(request):
    return render(request, 'Jpage/Jpage.html')

def get_data(request):
    # 모든 대분류 데이터를 가져옴
    largecategories = categoryCode1.objects.all()
    Areacodes = areaCode.objects.all()
    Places = areaBaseList.objects.all()

    # 선택된 대분류의 코드 가져오기 (예: GET 파라미터를 통해 전달됨)
    selected_cat1_code = request.GET.get('cat1_code')

    # 선택된 대분류 코드와 일치하는 중분류 데이터만 가져옴
    print(selected_cat1_code,categoryCode2.objects.filter(cat1_code=selected_cat1_code).values('code', 'name'))
    if selected_cat1_code:
        middlecategories = categoryCode2.objects.filter(cat1_code=selected_cat1_code).values('code', 'name')
    else:
        middlecategories = categoryCode2.objects.none()  # 아무 것도 선택되지 않은 경우 빈 쿼리셋

    selected_cat2_code = request.GET.get('cat2_code')

    print(selected_cat2_code, categoryCode3.objects.filter(cat2_code=selected_cat2_code).values('code', 'name'))
    if selected_cat1_code:
        smallcategories = categoryCode3.objects.filter(cat2_code=selected_cat2_code).values('code', 'name')
    else:
        smallcategories = categoryCode3.objects.none()  # 아무 것도 선택되지 않은 경우 빈 쿼리셋

    selected_areacode = request.GET.get('areacode')

    print(selected_areacode, cityDistrict.objects.filter(areacode=selected_areacode).values('code', 'name'))
    if selected_areacode:
        citydistricts = cityDistrict.objects.filter(areacode=selected_areacode).values('code', 'name')
    else:
        citydistricts = cityDistrict.objects.none()

    area_code = request.GET.get('area_code')
    city_code = request.GET.get('city_code')
    category_code = request.GET.get('category_code')

    print(city_code, category_code, areaBaseList.objects.filter(sigungucode=city_code, cat3=category_code).values('title'))
    if city_code and category_code:
        places = areaBaseList.objects.filter(areacode=area_code, sigungucode=city_code, cat3=category_code).values('title')
    else:
        places = areaBaseList.objects.none()

    place_name = request.GET.get('placeName')
    if place_name:
        coordinates = areaBaseList.objects.filter(title = place_name).values('mapx', 'mapy')
    else:
        coordinates = []


    # 컨텍스트에 대분류와 중분류 데이터를 추가
    context = {
        'largecategories': largecategories,
        'middlecategories': middlecategories,
        'smallcategories' : smallcategories,
        'Areacodes': Areacodes,
        'citydistricts': citydistricts,
        'places': places,
        'coordinates': coordinates
    }

    # 템플릿 렌더링
    return render(request, 'Jpage/map.html', context)

def get_middle_category(request):
    # 선택된 대분류 코드 가져오기
    selected_cat1_code = request.GET.get('cat1_code')

    # 선택된 대분류 코드와 일치하는 중분류 데이터만 필터링하여 가져오기
    if selected_cat1_code:
        middle_categories = categoryCode2.objects.filter(cat1_code=selected_cat1_code).values('code', 'name')
    else:
        middle_categories = []

    # JSON 응답으로 변환하여 반환
    print("get_middle_category : ",middle_categories)
    return JsonResponse({'middlecategories': list(middle_categories)})

def get_small_category(request):
    # 선택된 대분류 코드 가져오기
    selected_cat2_code = request.GET.get('cat2_code')

    # 선택된 대분류 코드와 일치하는 중분류 데이터만 필터링하여 가져오기
    if selected_cat2_code:
        small_categories = categoryCode3.objects.filter(cat2_code=selected_cat2_code).values('code', 'name')
    else:
        small_categories = []

    # JSON 응답으로 변환하여 반환
    print("get_small_category : ",small_categories)
    return JsonResponse({'smallcategories': list(small_categories)})

def get_cityDistrict(request):
    # 선택된 대분류 코드 가져오기
    selected_areacode = request.GET.get('areacode')

    # 선택된 대분류 코드와 일치하는 중분류 데이터만 필터링하여 가져오기
    if selected_areacode:
        city_districts = cityDistrict.objects.filter(areacode=selected_areacode).values('code', 'name')
    else:
        city_districts = []

    # JSON 응답으로 변환하여 반환
    print("get_cityDistrict : ",city_districts)
    return JsonResponse({'citydistricts': list(city_districts)})

def get_places(request):
    area_code = request.GET.get('area_code')
    city_code = request.GET.get('city_code')
    category_code = request.GET.get('category_code')
    if city_code and category_code:
        places = areaBaseList.objects.filter(areacode=area_code, sigungucode=city_code, cat3=category_code).values('title')
    else:
        places = []

    print("get_places : ", places)
    return JsonResponse({'places': list(places)})

def get_coordinate(request):
    place_name = request.GET.get('placeName')

    if place_name:
        coordinates = areaBaseList.objects.filter(title=place_name).values('mapx', 'mapy').first()
    else:
        coordinates = None

    print("get_coordinate:", coordinates)
    if coordinates:
        return JsonResponse({'mapx': coordinates['mapx'], 'mapy': coordinates['mapy']})
    else:
        return JsonResponse({'error': 'Place not found'}, status=404)

@csrf_exempt
def get_Jplan(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            print("Received data:", data)
            plan_id = data.get('plan_id')
            city = data.get('city')
            province = data.get('province')
            plan_title = data.get('plan_title')
            email = data.get('email')
            places = data.get('places')

            if city and province:
                plan = jPlan(
                    plan_id=plan_id,
                    province=province,
                    city=city,
                    plan_title=plan_title,
                    email=email,
                    days=places
                )
                document = plan.to_dict()
                result = db['plan'].insert_one(document)  # MongoDB에 저장
                return JsonResponse({"message": "Location saved successfully", "id": str(result.inserted_id)},
                                    status=200)
            else:
                return JsonResponse({"message": "Invalid data"}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({"message": "Invalid JSON"}, status=400)
    return JsonResponse({"message": "Method not allowed"}, status=405)

def user_info_view(request: HttpRequest, user_email=None):
    user_info = get_user(request, user_email)
    return render(request, 'map.html', user_info)


