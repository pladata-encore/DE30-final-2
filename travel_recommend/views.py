from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from pymongo import MongoClient
from django.conf import settings
from .forms import UserPreferencesForm
from django.views.decorators.csrf import csrf_exempt
import requests
import json

# MongoDB 클라이언트 설정
client = MongoClient(settings.DATABASES['default']['CLIENT']['host'])
db = client['MyDiary']
city_district_collection = db['cityDistrict']
area_code_collection = db['areaCode']


@csrf_exempt
def recommend(request):
    regions = get_regions()
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            form = UserPreferencesForm(data)
            if form.is_valid():
                payload = {
                    'region': form.cleaned_data['region'],
                    'subregion': form.cleaned_data['subregion'],
                    'start_date': form.cleaned_data['start_date'].strftime('%Y-%m-%d'),
                    'end_date': form.cleaned_data['end_date'].strftime('%Y-%m-%d'),
                    'travel_date': form.cleaned_data['travel_date'].split(' ~ '),
                    'pets_allowed': form.cleaned_data['pets_allowed'],
                    'pet_size': form.cleaned_data['pet_size'],
                    'food_preference': form.cleaned_data['food_preference'],
                    'tour_type': form.cleaned_data['tour_type'],
                    'accommodation_type': form.cleaned_data['accommodation_type'],
                    'travel_preference': form.cleaned_data['travel_preference']
                }
                response = requests.post('http://127.0.0.1:8001/recommend', json=payload)
                if response.status_code == 200:
                    recommendations = response.json()
                    request.session['recommendations'] = recommendations
                    return JsonResponse({'redirect_url': '/results'}, status=200)
                else:
                    form.add_error(None, "추천 요청에 실패했습니다. 다시 시도해주세요.")

        except json.JSONDecodeError:
            form = UserPreferencesForm()

    else:
        form = UserPreferencesForm()

    return render(request, 'recommendations/create_schedule.html', {'form':form, 'regions': regions})

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


def results(request):
    recommendations = request.session.get('recommendations', [])
    return render(request, 'results.html', {'recommendations': recommendations})


def index(request):
    return HttpResponse("Hello World!")