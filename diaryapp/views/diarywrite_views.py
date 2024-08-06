import os
import openai
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
from ..mongo_queries import filter_diaries


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

"""GPT3로 일기 생성"""
def generate_diary(request, plan_id=None):
    print(f'-------------여기가 generate 00번-------------{plan_id}')
    if request.method == 'POST':
        start_time = time.time()
        form = DiaryForm(request.POST, request.FILES)
        image_form = ImageUploadForm(request.POST, request.FILES)

        if form.is_valid() and image_form.is_valid():
            print(f'-------------여기가 generate 01번-------------{plan_id}')
            plan_id = request.session.pop('plan_id', None)
            print(f'-------------여기가 generate post session-------------{plan_id}')

            diarytitle = form.cleaned_data['diarytitle']
            place = form.cleaned_data['place']
            emotion = form.cleaned_data['emotion']
            withfriend = form.cleaned_data['withfriend']
            representative_image = request.FILES.get('image_file')

            user_email = settings.DEFAULT_FROM_EMAIL
            # user_email = request.user.email

            # place 번역
            #translated_place = translate_to_English(place)

            # # CLIP 모델과 전처리기 로드
            # model_info = open_clip.create_model_and_transforms('ViT-B-32', pretrained='openai')
            #
            # # 적절한 반환 값을 사용하도록 수정
            # clip_model = model_info[0]
            # preprocess = model_info[1]

            image = Image.open(representative_image)
            image = image.resize((128, 128), Image.LANCZOS)
            processed_image = preprocess(image).unsqueeze(0)

            CLIP_start_time = time.time()
            # 이미지 설명 후보 생성
            descriptions = generate_dynamic_descriptions()

            # 설명 후보들을 CLIP 모델로 처리
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
            prompt = (
                f"Please draft my travel diary based on this information. "
                f"I recently visited {place} in korea and I felt a strong sense of {emotion}. "
                f"One of the notable experiences was {best_description}.I want answers in Korean. I hope it's about 5sentences long")

            # GPT-3.5 모델을 사용하여 다이어리 생성
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

            # emotion 번역
            translated_emotion = translate_to_korean(emotion)

            # 일기 저장
            unique_diary_id = f"{timezone.now().strftime('%Y%m%d%H%M%S')}{diarytitle}"
            diary_entry = AiwriteModel.objects.create(
                unique_diary_id=unique_diary_id,
                user_email=user_email,
                diarytitle=diarytitle,
                place=place,
                emotion=translated_emotion,
                withfriend=withfriend,
                content=GPT3content,
            )
            diary_entry.save()

            # 별명 : 별명 생성
            # 나중에 일정 plan_id도 넘길 예정
            # 나중에 user 정보 넘길 예정
            print(f'-------------여기는 generate 작성 닉네임 쪽-------------{plan_id}')

            nickname_id = create_nickname(unique_diary_id, user_email, GPT3content, plan_id)
            # 별명 : 세션에 show_modal 저장
            request.session['show_modal'] = True
            # 별명 : 다이어리에 별명 ID 저장
            diary_entry.nickname_id = nickname_id
            diary_entry.save()


            image_start_time = time.time()

            # 추가 이미지 처리
            images = request.FILES.getlist('images')
            for img in images:
                additional_image_model = ImageModel(is_representative=False)
                additional_image_model.save_image(Image.open(img))
                additional_image_model.save()
                diary_entry.images.add(additional_image_model)  # ManyToMany 관계 설정

            # 대표 이미지 처리
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
                'redirect_url': f"{reverse('detail_diary_by_id', kwargs={'unique_diary_id': unique_diary_id})}",
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })
    else:
        form = DiaryForm()
        image_form = ImageUploadForm()

    return render(request, 'diaryapp/write_diary.html', {'form': form, 'image_form': image_form, 'plan_id': plan_id})

# 직접 일기 부분 작성
"""사용자가 일기 작성"""
def write_diary(request, plan_id=None):
    print(f'-------------여기가 다이어리 00번-------------{plan_id}')
    request.session['plan_id'] = plan_id
    print(f'-------------여기가 session-------------{plan_id}')

    if request.method == 'POST':
        form = DiaryForm(request.POST, request.FILES)
        image_form = ImageUploadForm(request.POST, request.FILES)
        plan_id = request.POST.get('plan_id', plan_id)
        print(f'-------------여기가 다이어리 01번-------------{plan_id}')
        plan_id = request.session.pop('plan_id', None)
        print(f'-------------여기가 write post session-------------{plan_id}')

        if form.is_valid() and image_form.is_valid():
            diarytitle = form.cleaned_data['diarytitle']
            place = form.cleaned_data['place']
            withfriend = form.cleaned_data['withfriend']
            content = form.cleaned_data['content']

            # writer = request.user.social_id
            user_email = settings.DEFAULT_FROM_EMAIL

            # # 태그된 사용자 목록에 다이어리 추가
            # tags = form.cleaned_data['withfriend'].split()
            # for tag in tags:
            #     try:
            #         user = User.objects.get(username=tag)  # social_id를 username으로 사용
            #         user.diaries.add(diary)
            #         user.save()
            #     except User.DoesNotExist:
            #         pass  # 비회원 처리

            # 일기 저장
            unique_diary_id = f"{timezone.now().strftime('%Y%m%d%H%M%S')}{diarytitle}"
            diary_entry = AiwriteModel.objects.create(  # 저장되는 다이어리
                unique_diary_id=unique_diary_id,
                user_email=user_email,
                diarytitle=diarytitle,
                place=place,
                withfriend=withfriend,
                # friends=friends,
                content=content,
            )
            diary_entry.save()


            # 별명 : 별명 생성
            # 나중에 일정 plan_id도 넘길 예정
            # 나중에 user 정보 넘길 예정
            print(f'-------------여기는 다이어리 작성 닉네임 쪽-------------{plan_id}')
            nickname_id = create_nickname(unique_diary_id, user_email, content, plan_id)
            # 별명 : 세션에 show_modal 저장
            request.session['show_modal'] = True
            # 별명 : 다이어리에 별명 ID 저장
            diary_entry.nickname_id = nickname_id
            diary_entry.save()


            # 대표 이미지 처리
            representative_image = request.FILES.get('image_file')
            if representative_image:
                image_model = ImageModel(is_representative=True)
                image_model.save_image(Image.open(representative_image))
                image_model.save()
                diary_entry.representative_image = image_model
                diary_entry.save()

            # 추가 이미지 처리
            images = request.FILES.getlist('images')
            for img in images:
                additional_image_model = ImageModel(is_representative=False)
                additional_image_model.save_image(Image.open(img))
                additional_image_model.save()
                diary_entry.images.add(additional_image_model)  # ManyToMany 관계 설정

            return JsonResponse({
                'success': True,
                'redirect_url': f"{reverse('detail_diary_by_id', kwargs={'unique_diary_id': unique_diary_id})}",
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })
    else:
        form = DiaryForm()
        image_form = ImageUploadForm()

    return render(request, 'diaryapp/write_diary.html', {'form': form, 'image_form': image_form, 'plan_id': plan_id})

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
# def list_user_diary(request):
#     user = request.user
#     diary_list = AiwriteModel.objects.filter(writer=user).order_by('-created_at')
#     return render(request, 'diaryapp/user_list_diary.html', {'diary_list': diary_list})

# 태그된 다이어리까지 전부 가져오기
# @login_required
# def tag_list_user_diary(request):
#     user = request.user
#     write_diary = AiwriteModel.objects.filter(writer=user).order_by('-created_at')
#     tag_diary = AiwriteModel.objects.filter(tags__name__startswith='@').filter(tags__name__in=[tag.name for tag in user.tags.all()]).exclude(writer=user).order_by('-created_at')
#
#
#     # 쓴 다이어리, 태그한 다이어리 따로 불러오기
#     # context = {
#     #     'write_diary': write_diary,
#     #     'tag_diary': tag_diary
#     # }
#
#     # 쓴 다이어리, 태그한 다이어리 합쳐서 시간 순으로 불러오기
#     diary = (write_diary | tag_diary).order_by('-created_at')
#     context = {
#         'diary' : diary
#     }
#     return render(request, 'diaryapp/user_list_diary.html', context)

'''일기 내용 확인'''
def detail_diary_by_id(request, unique_diary_id):
    # user_email = request.user.email
    user_email = settings.DEFAULT_FROM_EMAIL
    diary = get_object_or_404(AiwriteModel, unique_diary_id=unique_diary_id)
    form = CommentForm()
    comment_list = CommentModel.objects.filter(diary_id=diary).order_by('-created_at')
    # tagged_users = diary.get_tagged_users()
    # return render(request, 'diaryapp/detail_diary.html', {'diary': diary, 'tagged_users': tagged_users})
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
    return render(request, 'diaryapp/plan_modal.html', {'diary': diary})

'''
user가 생기면 변경 - 로그인한 사용자를 기준으로 본인의 일기와 다른 사용자의 일기를 볼 때 화면이 다름
'''
# @login_required
# def detail_diary_by_id(request, unique_diary_id):
#     user = request.user
#     diary = get_object_or_404(AiwriteModel, unique_diary_id=unique_diary_id)
#     # tagged = diary.get_tagged_users()
#     # comments = diary.comments.all()
#     if diary.writer == user:
#         template = 'diaryapp/detail_diary.html'
#     else:
#         template = 'diaryapp/detail_diary_otheruser.html'
#     context = {
#         'diary':diary,
#         # 'tagged':tagged,
#         # 'comments':comments
#     }
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
