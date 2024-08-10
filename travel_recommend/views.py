import logging
import uuid

from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from pymongo import MongoClient
from django.conf import settings
from .forms import UserPreferencesForm
from django.views.decorators.csrf import csrf_exempt
import requests
import json
from datetime import datetime

# MongoDB 클라이언트 설정
client = MongoClient(settings.DATABASES['default']['CLIENT']['host'])
db = client['MyDiary']
city_district_collection = db['cityDistrict']
area_code_collection = db['areaCode']

logger = logging.getLogger(__name__)

@csrf_exempt
def recommend(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            logger.info(f"Received data: {data}")

            # CSRF 토큰 제거
            if 'csrfmiddlewaretoken' in data:
                del data['csrfmiddlewaretoken']

            # 데이터 유효성 검사 및 수정
            if 'tour_type' in data:
                data['tour_type'] = [item.strip() for item in data['tour_type'] if item.strip()]
            if 'food_preference' in data:
                data['food_preference'] = [item.strip() for item in data['food_preference'] if item.strip()]
            if 'accommodation_type' in data:
                data['accommodation_type'] = [item.strip() for item in data['accommodation_type'] if item.strip()]
            if 'travel_preference' in data:
                data['travel_preference'] = data['travel_preference'].strip()

            print(f"DATA: {data}")

            form = UserPreferencesForm(data)
            if form.is_valid():
                response = requests.post('http://localhost:5000/recommend', json=data)
                response_data = response.json()
                logger.info(f"Response from FastAPI: {response_data}")

                if response.status_code == 200:
                    plan_id = response_data.get('plan_id')
                    if plan_id:
                        logger.info(f"Returning plan_id: {plan_id}")
                        return JsonResponse({'plan_id': plan_id})
                    else:
                        return JsonResponse({'error': 'No plan_id returned from FAstAPI'}, status=500)
                else:
                    return JsonResponse({'error': 'Failed to get recommendations from FastAPI'}, status=response.status_code)
            else:
                return JsonResponse({'error': 'Invalid form data'}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            logger.error(f"Error: {e}")
            return JsonResponse({'error': str(e)}, status=500)
    else:
        form = UserPreferencesForm()
        regions = list(area_code_collection.find())
        return render(request, 'recommendations/create_schedule.html', {'form': form, 'regions': regions})


def get_regions():
    regions = list(area_code_collection.find())
    return [{"code": region['code'], "name": region['name']} for region in regions]

@csrf_exempt ## 로그인 완성되면 @login_required 데코레이터로 변경해주기
def load_subregions(request):
    region_code = request.GET.get('region')
    if region_code and region_code.isdigit():
        subregions = list(city_district_collection.find({'areacode': region_code}))
        response_data = [{'id': subregion['code'], 'name': subregion['name']} for subregion in subregions]
        return JsonResponse(response_data, safe=False)
    return JsonResponse({'error': 'Region code is required and must be a number'}, status=400)


# FastAPI로부터 받은 응답을 db에 저장하고 result 페이지에 렌더링
def results(request, plan_id):
    try:
        logger.info(f"Fetching plan with plan_id: {plan_id}")
        # FastAPI 서버에서 일정 정보 가져옴
        response = requests.get(f'http://localhost:5000/plan/{plan_id}')
        logger.info(f"^^^^^^^^^Response from FastAPI for plan_id: {response}")
        response_data = response.json()
        logger.info(f"Response from FastAPI for plan_id {plan_id}: {response_data}")

        # Itinerary 데이터에서 mapx, mapy 필드가 포함되어 있는지 확인
        for day in response_data.get('itinerary', []):
            for recommendation in day.get('recommendations', []):
                logger.info(f"Title: {recommendation['title']}, MapX: {recommendation.get('mapx')}, MapY: {recommendation.get('mapy')}")



        if response.status_code == 200:
            itinerary = response_data.get('itinerary')
            logger.info(f"Fetched itinerary: {itinerary}")  # 로깅 추가

            logger.info("Rendering result.html with itinerary data")
            response = render(request, 'recommendations/result.html', {'itinerary': itinerary,'plan_id': plan_id})
            logger.info("Rendered result.html successfully")
            return response
        else:
            logger.error(f"Failed to fetch itinerary from FastAPI: {response.status_code}")
            return render(request, 'recommendations/error.html', {'message': "Failed to load itinerary"})
    except Exception as e:
        logger.error(f"Error fetching itinerary: {e}")
        return render(request, 'recommendations/error.html', {'message': "An error occurred while fetching itinerary"})

# 추천 결과 페이지에서 보여주는 여행 장소 정보 (모달을 통해 보여주는 정보)

def get_place_details(request, contentid):
    # MongoDB 연결 설정
    # client = MongoClient('mongodb://127.0.0.1:27017/')
    # db = client['MyDiary']
    from django.conf import settings
    db = settings.MONGO_CLIENT[settings.DATABASES['default']['NAME']]

    collections = [
        db.accommodations,
        db.areaBaseList12,
        db.areaBaseList14,
        db.areaBaseList28,
        db.areaBaseList38,
        db.areaBaseList39
    ]

    place_details = None
    for collection in collections:
        place_details = collection.find_one({"contentid": contentid})
        if place_details:
            break

    if not place_details:
        return JsonResponse({'error': 'Place not found'}, status=404)

    response_data = {
        "title": place_details.get("title"),
        "addr1": place_details.get("addr1"),
        "addr2": place_details.get("addr2"),
        "firstimage": place_details.get("firstimage"),
        "overview": place_details.get("overview")
    }

    return JsonResponse(response_data)



# 사용자 일정 불러오기
def view_schedule(request):
    user_id = request.GET.get('user_id')
    schedules = list(db.schedules.find({'user_id': user_id}))

    return render(request, 'recommendations/view_schedule.html', {'schedules': schedules})

# 메인 페이지
def index(request):
    return render(request, 'service_main.html')

def test_redirect(request):
    return redirect('results', plan_id='651a7290-8989-447b-8357-2566c4728e25')