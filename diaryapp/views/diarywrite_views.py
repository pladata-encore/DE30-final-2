import os
import openai
from django.contrib.auth.decorators import login_required
from dotenv import load_dotenv
import gridfs
import torch
import open_clip
from PIL import Image
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from pymongo import MongoClient
from torchvision import transforms
from transformers import GPT2LMHeadModel, GPT2Tokenizer
from django.shortcuts import render, get_object_or_404, redirect
from myproject import settings
from .badge_views import get_main_badge
from ..forms import *
from ..models import *
from ..clip_model import *
from diaryapp.forms import *
import base64
import time
from django.conf import settings

from django.forms.models import modelformset_factory
from django.contrib.auth.models import User
from .nickname_views import *

from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from ..mongo_queries import filter_diaries, get_plan_by_id, get_available_plans as mongo_get_available_plans


# MongoDB 클라이언트 설정
db = settings.MONGO_CLIENT[settings.DATABASES['default']['NAME']]

# 컬렉션
collection = db['diaryapp_nickname']

"""GPT3.5 키"""
load_dotenv()
openai.api_key = os.getenv("OPEN_API_KEY")

"""태그된 사용자 자동 완성 기능"""
# def user_suggestions(request):
#     query = request.GET.get('query', '')
#     users = User.objects.filter(username__icontains=query)  # 사용자가 'social_id'로 정의되어 있다면 필드를 변경하세요.
#     suggestions = [{'username': user.username} for user in users]
#     return JsonResponse({'suggestions': suggestions})

"""GPT3.5 처리에 필요한 코드들"""
def image_detail(request, pk):
    image_model = ImageModel.objects.get(pk=pk)
    image_data = base64.b64decode(image_model.image_file)
    return HttpResponse(image_data, content_type="image/png")
def generate_dynamic_descriptions():
    descriptions = [
        "dog", "park", "cat", "sunset", "ocean", "island", 'Village', 'Campsite', 'Lodge', "Safari", "Fountain",
        "street", "landscape", "mountain", "tree", "flow", "friends", "picnic", 'Cottage', "Cruise", "Square",
        "bridge", "sky", "market", "fruits", "vegetables", "Theme park", "Amusement park", "Aquarium", "Plaza",
        "beach", "sea", "coffee", " books", "cafe", "family", " zoo", "Botanical garden", "National park",
        "couple", "castle", "flower", "street", "village", "bridge", "Harbor", "Port", "River", "Waterfall",
        "Promenade", "Viewpoint", "Lighthouse", "Monument", "Memorial", "Statue", "Landmark", "Tower", "Arena",
        "Stadium", "Pasture", "Orchard", "Brewery", "Winery", "Distillery", "Fair", "Carnival", "Parade", "Festival",
        "Hiking trail", "Bike trail", "Ski slope", "Golf course"
    ]
    return descriptions
def translate_to_korean(text): # 일기 내용 한국어로 번역
    translator = Translator()
    translated = translator.translate(text, src='en', dest='ko')
    return translated.text


def get_plan_place(request, plan_id):
    plan = get_plan_by_id(plan_id)
    if plan:
        place = f"{plan.get('province', '')} {plan.get('city', '')}".strip()
        return JsonResponse({'place': place})
    return JsonResponse({'place': ''})

"""GPT3로 일기 생성"""
def generate_diary(request, plan_id=None):
    if request.method == 'POST':
        start_time = time.time()
        form = DiaryForm(request.POST, request.FILES)
        image_form = ImageUploadForm(request.POST, request.FILES)

        if form.is_valid() and image_form.is_valid():
            if not plan_id:
                # return JsonResponse({'success': False, 'errors': 'No plan_id provided'}, status=400)
                print(f'-------------여기가 generate 01번-------------{plan_id}')
                plan_id = request.session.pop('plan_id', None)
                print(f'-------------여기가 generate post session-------------{plan_id}')

            plan = get_plan_by_id(plan_id)
            if not plan:
                return JsonResponse({'success': False, 'errors': 'Invalid plan_id'}, status=400)

            place = f"{plan.get('province', '')} {plan.get('city', '')}".strip() if plan else "Unknown location"
            diarytitle = form.cleaned_data['diarytitle']
            emotion = form.cleaned_data['emotion']
            withfriend = form.cleaned_data['withfriend']
            representative_image = request.FILES.get('image_file')

            # user_email = settings.DEFAULT_FROM_EMAIL
            user_email = 'neweeee@gmail.com'

            image = Image.open(representative_image)
            image = image.resize((128, 128), Image.LANCZOS)
            processed_image = preprocess(image).unsqueeze(0)
            CLIP_start_time = time.time()

            descriptions = generate_dynamic_descriptions()
            tokens = open_clip.tokenize(descriptions)
            with torch.no_grad():
                image_features = clip_model.encode_image(processed_image)
                text_features = clip_model.encode_text(tokens)
                similarity = torch.softmax((100.0 * image_features @ text_features.T), dim=-1)
                best_description_idx = similarity.argmax().item()
                best_description = descriptions[best_description_idx]
            CLIP_end_time = time.time()
            print('------------- CLIP image --------', CLIP_end_time - CLIP_start_time)

            GPT_start_time = time.time()
            if plan:
                place = f"{plan.get('province', '')} {plan.get('city', '')}".strip()
            else:
                place = "Unknown location"

            prompt = (
                f"Please draft my travel diary based on this information. "
                f"I recently visited {place} in Korea and I felt a strong sense of {emotion}. "
                f"One of the notable experiences was {best_description}. I want answers in Korean. I hope it's about 5 sentences long.")

            completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=400,
                temperature=1
            )
            GPT3content = completion['choices'][0]['message']['content']

            GPT_end_time = time.time()
            print('------------- gpt image --------', GPT_end_time - GPT_start_time)


            translated_emotion = translate_to_korean(emotion)

            unique_diary_id = f"{timezone.now().strftime('%Y%m%d%H%M%S')}{diarytitle}"
            diary_entry = AiwriteModel.objects.create(
                unique_diary_id=unique_diary_id,
                user_email=user_email,
                diarytitle=diarytitle,
                plan_id=plan_id,
                emotion=translated_emotion,
                withfriend=withfriend,
                content=GPT3content,
                place=place
            )
            diary_entry.save()

            nickname_id = create_nickname(unique_diary_id, user_email, GPT3content, plan_id)
            request.session['show_modal'] = True
            diary_entry.nickname_id = nickname_id
            diary_entry.save()

            image_start_time = time.time()

            images = request.FILES.getlist('images')
            for img in images:
                additional_image_model = ImageModel(is_representative=False)
                additional_image_model.save_image(Image.open(img))
                additional_image_model.save()
                diary_entry.images.add(additional_image_model)

            if representative_image:
                image_model = ImageModel(is_representative=True)
                image_model.save_image(Image.open(representative_image))
                image_model.save()
                diary_entry.representative_image = image_model
                diary_entry.save()

            image_end_time = time.time()
            print('------------- get image --------', image_end_time - image_start_time)
            end_time = time.time()
            print('------------- total end --------', end_time - start_time)

            return JsonResponse({
                'success': True,
                'redirect_url': reverse('detail_diary_by_id', kwargs={'unique_diary_id': unique_diary_id}),
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })
    else:
        form = DiaryForm()
        image_form = ImageUploadForm()

        plan = get_plan_by_id(plan_id) if plan_id else None
        place = f"{plan.get('province', '')} {plan.get('city', '')}".strip() if plan else ""

        context = {
            'form': form,
            'image_form': image_form,
            'plan_id': plan_id,
            'place': place
        }
        return render(request, 'diaryapp/write_diary.html', context)


"""사용자가 일기 작성"""
def write_diary(request, plan_id=None):
    if request.method == 'POST':
        print(f'-------------여기가 다이어리 00번-------------{plan_id}')

        form = DiaryForm(request.POST, request.FILES)
        image_form = ImageUploadForm(request.POST, request.FILES)

        # currentPlanId 또는 plan_id 가져오기
        currentPlanId = request.POST.get('plan_id', None)

        if currentPlanId:
            # currentPlanId가 있으면 세션에 저장
            request.session['plan_id'] = currentPlanId
            print(f'-------------여기가  폼 currentPlanId session-------------{currentPlanId}')
        elif plan_id:
            # plan_id가 있으면 세션에 저장
            request.session['plan_id'] = plan_id
            print(f'-------------여기가 주소 plan_id session-------------{plan_id}')


        if form.is_valid() and image_form.is_valid():
            plan_id = currentPlanId or plan_id
            if not plan_id:
                # return JsonResponse({'success': False, 'errors': 'No plan_id provided'}, status=400)
                print(f'-------------여기가 다이어리 01번-------------{plan_id}')
                plan_id = request.session.pop('plan_id', None)
                print(f'-------------여기가 write post session-------------{plan_id}')

            plan = get_plan_by_id(plan_id)
            if not plan:
                return JsonResponse({'success': False, 'errors': 'Invalid plan_id'}, status=400)

            place = f"{plan.get('province', '')} {plan.get('city', '')}".strip()

            diarytitle = form.cleaned_data['diarytitle']
            withfriend = form.cleaned_data['withfriend']
            content = form.cleaned_data['content']

            # user_email = request.user.email  # 사용자 이메일을 현재 로그인한 사용자의 이메일로 가져옵니다.
            user_email = 'neweeee@gmail.com'

            unique_diary_id = f"{timezone.now().strftime('%Y%m%d%H%M%S')}{diarytitle}"
            diary_entry = AiwriteModel.objects.create(
                unique_diary_id=unique_diary_id,
                user_email=user_email,
                diarytitle=diarytitle,
                withfriend=withfriend,
                plan_id=plan_id,
                content=content,
                place=place
            )
            diary_entry.save()
            print(f"Saved diary entry: {diary_entry.id}, place: {diary_entry.place}")

            nickname_id = create_nickname(unique_diary_id, user_email, content, plan_id)
            request.session['show_modal'] = True
            diary_entry.nickname_id = nickname_id
            diary_entry.save()

            representative_image = request.FILES.get('image_file')
            if representative_image:
                image_model = ImageModel(is_representative=True)
                image_model.save_image(Image.open(representative_image))
                image_model.save()
                diary_entry.representative_image = image_model
                diary_entry.save()

            images = request.FILES.getlist('images')
            for img in images:
                additional_image_model = ImageModel(is_representative=False)
                additional_image_model.save_image(Image.open(img))
                additional_image_model.save()
                diary_entry.images.add(additional_image_model)

            return JsonResponse({
                'success': True,
                'redirect_url': reverse('detail_diary_by_id', kwargs={'unique_diary_id': unique_diary_id}),
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })
    else:
        form = DiaryForm()
        image_form = ImageUploadForm()

        plan = get_plan_by_id(plan_id) if plan_id else None
        place = f"{plan.get('province', '')} {plan.get('city', '')}".strip() if plan else ""

        context = {
            'form': form,
            'image_form': image_form,
            'plan_id': plan_id,
            'place': place
        }
        return render(request, 'diaryapp/write_diary.html', context)


'''전체 일기 리스트'''
def list_diary(request):
    form = DateFilterForm(request.GET or None)
    year = None
    month = None
    if form.is_valid():
        year = form.cleaned_data['year']
        month = form.cleaned_data['month']

    diary_list = filter_diaries(year, month)
    print(f"Diaries returned to view: {len(diary_list)}")

    # 페이징 설정
    paginator = Paginator(diary_list, 9)  # 한 페이지에 9개의 일기를 보여줍니다 (3x3 그리드)
    page_number = request.GET.get('page')

    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    enriched_diary_list = []

    for diary in page_obj:
        print(f"Processing diary with unique_diary_id: {diary.get('unique_diary_id')}")
        try:
            # diary_model = AiwriteModel.objects.get(unique_diary_id=diary.get('unique_diary_id'))
            # nickname_id, nickname, badge_name, badge_image = get_nickname(diary_model.nickname_id)
            diary_model = get_object_or_404(AiwriteModel, unique_diary_id=diary.get('unique_diary_id'))
            if diary_model.nickname_id == '<JsonResponse status_code=500, "application/json">':
                nickname_id, nickname, badge_name, badge_image = '', '별명이 없습니다.', '', ''
            else:
                nickname_id, nickname, badge_name, badge_image = get_nickname(diary_model.nickname_id)
            enriched_diary = {
                'diary': diary,
                'nickname': nickname,
                'badge_name': badge_name,
                'badge_image': badge_image
            }
            enriched_diary_list.append(enriched_diary)
        except AiwriteModel.DoesNotExist:
            print(f"AiwriteModel not found for unique_diary_id: {diary.get('unique_diary_id')}")
            # 여기서 오류를 무시하고 계속 진행하거나,
            # 필요에 따라 기본값을 설정할 수 있습니다.
            continue

        print(f"Diary in view: {diary.get('diarytitle', 'No title')}, "
              f"Created: {diary.get('created_at', 'No date')}, "
              f"Has Image: {'Yes' if diary.get('representative_image') else 'No'}")

    context = {
        'form': form,
        'diary_list': enriched_diary_list,
        'page_obj': page_obj,  # 템플릿에서 사용하는 이름으로 변경
    }

    return render(request, 'diaryapp/list_diary.html', context)


'''로그인한 사용자 확인 가능한 본인 일기 리스트'''
# @login_required
def list_user_diary(request):
    # user = request.user
    user_email = settings.DEFAULT_FROM_EMAIL
    form = DateFilterForm(request.GET or None)
    year = None
    month = None
    if form.is_valid():
        year = form.cleaned_data['year']
        month = form.cleaned_data['month']

    # 로그인한 사용자의 다이어리만 필터링
    diary_list = filter_user_diaries(user_email, year, month)
    print(f"Diaries returned to view: {len(diary_list)}")

    # 페이징 설정
    paginator = Paginator(diary_list, 9)  # 한 페이지에 9개의 일기를 보여줍니다 (3x3 그리드)
    page_number = request.GET.get('page')

    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    enriched_diary_list = []

    for diary in page_obj:
        print(f"Processing diary with unique_diary_id: {diary.unique_diary_id}")
        try:
            diary_model = get_object_or_404(AiwriteModel, unique_diary_id=diary.unique_diary_id, user_email=user_email)
            if diary_model.nickname_id == '<JsonResponse status_code=500, "application/json">':
                nickname, badge_name, badge_image = '별명이 없습니다.', '', ''
            else:
                nickname_id, nickname, badge_name, badge_image = get_nickname(diary_model.nickname_id)
            enriched_diary = {
                'diary': diary,
                'nickname': nickname,
                'badge_name': badge_name,
                'badge_image': badge_image
            }
            enriched_diary_list.append(enriched_diary)
        except AiwriteModel.DoesNotExist:
            print(f"AiwriteModel not found for unique_diary_id: {diary.unique_diary_id}")
            continue

        print(f"Diary in view: {diary.diarytitle}, Created: {diary.created_at}, Has Image: {'Yes' if diary.representative_image else 'No'}")

    context = {
        'form': form,
        'diary_list': enriched_diary_list,
        'page_obj': page_obj,
    }
    return render(request, 'diaryapp/user_list_diary.html', context)

def filter_user_diaries(user_email, year=None, month=None):
    diaries = AiwriteModel.objects.filter(user_email=user_email).order_by('-created_at')

    if year:
        diaries = diaries.filter(created_at__year=year)
    if month:
        diaries = diaries.filter(created_at__month=month)

    return diaries

'''일기 내용 확인'''
def detail_diary_by_id(request, unique_diary_id):
    # user_email = request.user.email
    user_email = settings.DEFAULT_FROM_EMAIL
    diary = get_object_or_404(AiwriteModel, unique_diary_id=unique_diary_id)
    form = CommentForm()
    comment_list = CommentModel.objects.filter(diary_id=diary).order_by('-created_at')

    # 각 댓글에 대한 사용자 정보 추가
    # for comment in comment_list:
    #     user = comment.user.first()
    #     if user:
    #         _, nickname, badge_name, badge_image = get_main_badge(user.email)
    #         comment.username = user.username
    #         comment.nickname = nickname
    #         comment.badge_name = badge_name
    #         comment.badge_image = badge_image
    #     else:
    #         comment.username = "Unknown"
    #         comment.nickname = "Unknown"
    #         comment.badge_name = "Unknown"
    #         comment.badge_image = ""

    for comment in comment_list:
        _, nickname, badge_name, badge_image = get_main_badge(comment.user_email)
        comment.nickname = nickname
        comment.badge_name = badge_name
        comment.badge_image = badge_image

    # 디버깅을 위해 댓글 수를 출력
    print(f"Number of comments: {comment_list.count()}")

    # 별명 : db에서 가져오기
    if diary.nickname_id == '<JsonResponse status_code=500, "application/json">':
        nickname, badge_name, badge_image = '별명이 없습니다.', '', ''
    else:
        nickname_id, nickname, badge_name, badge_image = get_nickname(diary.nickname_id)

    # 별명 : 세션에서 데이터 가져오기
    show_modal = request.session.pop('show_modal', False) # 테스트 : True로 해서 테스트

    context = {
        'diary': diary,
        'comment_list': comment_list,
        'form': CommentForm(),
        'show_modal': show_modal,
        'nickname': nickname,
        'badge_name': badge_name,
        'badge_image': badge_image,
    }
    return render(request, 'diaryapp/detail_diary.html', context)

'''다이어리 여행일정 모달 창'''
def plan_modal(request, unique_diary_id):
    diary = get_object_or_404(AiwriteModel, unique_diary_id=unique_diary_id)
    plan_id = diary.plan_id

    # plan 정보 가져오기
    plan = get_plan_by_id(plan_id) if plan_id else None

    if plan:
        province = plan.get('province', '')
        city = plan.get('city', '')
        plan_title = plan.get('plan_title', '')
        days = plan.get('days', {})
    else:
        province = city = plan_title = ''
        days = {}

    context = {
        'province': province,
        'city': city,
        'plan_title': plan_title,
        'days': days,
    }
    return JsonResponse(context)

'''
user가 생기면 변경 - 로그인한 사용자를 기준으로 자신이 작성한 일기와 다른 사용자가 작성한 일기를 볼 때 화면이 다름
'''
# @login_required
# def detail_diary_by_id(request, unique_diary_id):
#     user = request.user
#     diary = get_object_or_404(AiwriteModel, unique_diary_id=unique_diary_id)
#     form = CommentForm()
#     comment_list = CommentModel.objects.filter(diary_id=diary).order_by('-created_at')
#
#     # 디버깅을 위해 댓글 수를 출력
#     print(f"Number of comments: {comment_list.count()}")
#
#     # 별명 : db에서 가져오기
#     if diary.nickname_id == '<JsonResponse status_code=500, "application/json">':
#         nickname, badge_name, badge_image = '별명이 없습니다.', '', ''
#     else:
#         nickname, badge_name, badge_image = get_nickname(diary.nickname_id)
#
#     # 별명 : 세션에서 데이터 가져오기
#     show_modal = request.session.pop('show_modal', True)  # 테스트 : False로 변경 예정
#
#     context = {
#         'diary': diary,
#         'comment_list': comment_list,
#         'form': form,
#         'show_modal': show_modal,
#         'nickname': nickname,
#         'badge_name': badge_name,
#         'badge_image': badge_image,
#     }
#
#     # 사용자가 자신의 일기를 보는 경우와 다른 사용자의 일기를 보는 경우 템플릿 분기
#     if diary.writer == user:
#         template = 'diaryapp/detail_diary.html'
#     else:
#         template = 'diaryapp/detail_diary_otheruser.html'
#
#     return render(request, template, context)

'''일기 내용 업데이트'''
# @login_required # html에서 할 수 있으면 삭제
def update_diary(request, unique_diary_id):
    diary = get_object_or_404(AiwriteModel, unique_diary_id=unique_diary_id)

    if request.method == 'POST':

        # emotion 번역
        diary.diarytitle = request.POST['diarytitle']
        diary.place = request.POST['place']
        diary.withfriend = request.POST['withfriend']
        diary.content = request.POST['content']

        # user_email = request.user.email
        # from django.contrib.auth import authenticate, login
        # user = authenticate(request, username=username)
        user_email = settings.DEFAULT_FROM_EMAIL
        diary.save()

        # 대표 이미지 처리 (대표 이미지 변경)
        representative_image = request.FILES.get('image_file')
        if representative_image:
            if diary.representative_image:
                diary.representative_image.delete()  # 기존 대표 이미지 삭제
            image_model = ImageModel(is_representative=True)
            image_model.save_image(Image.open(representative_image))
            image_model.save()
            diary.representative_image = image_model
            diary.save()

        # 추가 이미지 처리
        images = request.FILES.getlist('images')
        for img in images:
            additional_image_model = ImageModel(is_representative=False)
            additional_image_model.save_image(Image.open(img))
            additional_image_model.save()
            diary.images.add(additional_image_model)  # ManyToMany 관계 설정

        # 기존 이미지 삭제 처리
        delete_image_ids = request.POST.getlist('delete_images')
        for image_id in delete_image_ids:
            image_to_delete = ImageModel.objects.get(id=image_id)
            diary.images.remove(image_to_delete)
            image_to_delete.delete()

        return redirect(reverse('detail_diary_by_id', kwargs={'unique_diary_id': unique_diary_id}))
    else:
        form = DiaryForm(instance=diary)
        image_form = ImageUploadForm()

    existing_images = diary.images.all()

    return render(request, 'diaryapp/update_diary.html', {
        'diary': diary,
        'existing_images': existing_images,
        'form': form,
        'image_form': image_form,
    })

'''일기 내용 삭제'''
# @login_required   # html에서 할 수 있으면 삭제
def delete_diary(request, unique_diary_id):
    # user_email = request.user.email
    user_email = settings.DEFAULT_FROM_EMAIL
    diary = get_object_or_404(AiwriteModel, unique_diary_id=unique_diary_id)

    if request.method == 'POST':
        diary.delete()
        nickname_collection.delete_one({"nickname_id": diary.nickname_id})
        return redirect('list_diary')
    return redirect('list_diary')