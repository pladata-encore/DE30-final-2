# diaryapp/views.py
import os
import openai
from dotenv import load_dotenv
import gridfs
import torch
import open_clip
from PIL import Image
from django.http import HttpResponse
from django.utils import timezone
from pymongo import MongoClient
from transformers import GPT2LMHeadModel, GPT2Tokenizer
from django.shortcuts import render, get_object_or_404, redirect
from myproject import settings
from .forms import *
from .models import *
from .storage import save_file_to_gridfs, get_file_from_gridfs, delete_file_from_gridfs, get_file_url_from_gridfs
from googletrans import Translator
import io
import base64
from django.forms.models import modelformset_factory

# GPTAPI키 가져오기
# load_dotenv()
# openai.api_key = "${OPEN_API_KEY}"

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

# 번역 API
def translate_to_korean(text): # 일기 내용 한국어로 번역
    translator = Translator()
    translated = translator.translate(text, src='en', dest='ko')
    return translated.text
def translate_to_English(text): # 입력한 감정,장소 영어로 번역
    translator = Translator()
    translated = translator.translate(text, src='ko', dest='en')
    return translated.text

# GPT API사용해서 일기 가져오는 부분
def generate_diary(request):
    if request.method == 'POST':
        form = DiaryForm(request.POST, request.FILES)
        image_form = ImageUploadForm(request.POST, request.FILES)

        if form.is_valid() and image_form.is_valid():
            diarytitle = form.cleaned_data['diarytitle']
            place = form.cleaned_data['place']
            emotion = form.cleaned_data['emotion']
            withfriend = form.cleaned_data['withfriend']
            content = form.cleaned_data['content']
            representative_image = request.FILES.get('image_file')

            user_email = settings.DEFAULT_FROM_EMAIL
            # user_email = request.user.email if request.user.is_authenticated else None

            # place 번역
            translated_place = translate_to_English(place)

            # CLIP 모델과 전처리기 로드
            model_info = open_clip.create_model_and_transforms('ViT-B-32', pretrained='openai')
            # print(model_info)  # 반환 값을 확인하기 위해 출력

            # 적절한 반환 값을 사용하도록 수정
            clip_model = model_info[0]
            preprocess = model_info[1]

            image = Image.open(representative_image)
            image = preprocess(image).unsqueeze(0)

            # 이미지 설명 후보 생성
            descriptions = generate_dynamic_descriptions()

            # 설명 후보들을 CLIP 모델로 처리
            tokens = open_clip.tokenize(descriptions)
            with torch.no_grad():
                image_features = clip_model.encode_image(image)
                text_features = clip_model.encode_text(tokens)
                similarity = torch.softmax((100.0 * image_features @ text_features.T), dim=-1)
                best_description_idx = similarity.argmax().item()
                best_description = descriptions[best_description_idx]

            korea_description = translate_to_korean(best_description)
            translated_emotion = translate_to_korean(emotion)
            prompt = (
                f"Please draft my travel diary based on this information. 'I recently visited {translated_place} in korea and i felt a strong sense of {emotion}. One of the notable experiences was {best_description}.' ")
            # GPT-2 모델을 사용하여 텍스트 생성
            model_name = "gpt2"
            model = GPT2LMHeadModel.from_pretrained(model_name)
            tokenizer = GPT2Tokenizer.from_pretrained(model_name)
            inputs = tokenizer.encode(prompt, return_tensors='pt')
            outputs = model.generate(inputs, max_length=1000, num_return_sequences=1, no_repeat_ngram_size=2,
                                     early_stopping=True)

            diary_text = tokenizer.decode(outputs[0], skip_special_tokens=True)

            # 프롬프트 내용 제외
            diary_text_parts = diary_text.split(prompt)
            if len(diary_text_parts) > 1:
                extracted_content = diary_text_parts[1].strip()
            else:
                extracted_content = diary_text.strip()

            translated_text = translate_to_korean(extracted_content)

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
                content=extracted_content,
            )
            diary_entry.save()

            # 대표 이미지 처리
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

            return redirect('list_diary', permanent=True)
        else:
            return render(request, 'diaryapp/list_diary.html', {'form': form, 'image_form': image_form})
    else:
        form = DiaryForm()
        image_form = ImageUploadForm()

    return render(request, 'diaryapp/write_diary.html', {'form': form, 'image_form': image_form})

"""GPT3로 일기 생성"""
# def generate_diary(request):
#     if request.method == 'POST':
#         form = DiaryForm(request.POST, request.FILES)
#         image_form = ImageUploadForm(request.POST, request.FILES)
#
#         if form.is_valid() and image_form.is_valid():
#             diarytitle = form.cleaned_data['diarytitle']
#             place = form.cleaned_data['place']
#             emotion = form.cleaned_data['emotion']
#             withfriend = form.cleaned_data['withfriend']
#             content = form.cleaned_data['content']
#             representative_image = request.FILES.get('image_file')
#
#             user_email = settings.DEFAULT_FROM_EMAIL
#             # user_email = request.user.email if request.user.is_authenticated else None
#
#             # place 번역
#             translated_place = translate_to_English(place)
#
#             # CLIP 모델과 전처리기 로드
#             model_info = open_clip.create_model_and_transforms('ViT-B-32', pretrained='openai')
#
#             # 적절한 반환 값을 사용하도록 수정
#             clip_model = model_info[0]
#             preprocess = model_info[1]
#
#             image = Image.open(representative_image)
#             image = preprocess(image).unsqueeze(0)
#
#             # 이미지 설명 후보 생성
#             descriptions = generate_dynamic_descriptions()
#
#             # 설명 후보들을 CLIP 모델로 처리
#             tokens = open_clip.tokenize(descriptions)
#             with torch.no_grad():
#                 image_features = clip_model.encode_image(image)
#                 text_features = clip_model.encode_text(tokens)
#                 similarity = torch.softmax((100.0 * image_features @ text_features.T), dim=-1)
#                 best_description_idx = similarity.argmax().item()
#                 best_description = descriptions[best_description_idx]
#
#             prompt = (
#                 f"Please draft my travel diary based on this information. "
#                 f"I recently visited {translated_place} in korea and I felt a strong sense of {emotion}. "
#                 f"One of the notable experiences was {best_description}.I want answers in Korean. I hope the answer doesn't exceed five lines")
#
#             # GPT-3.5 모델을 사용하여 다이어리 생성
#             completion = openai.ChatCompletion.create(
#                 model="gpt-3.5-turbo",
#                 messages=[
#                     {"role": "user", "content": prompt}
#                 ],
#                 max_tokens=1000,
#                 temperature=1
#             )
#             GPT3content = completion['choices'][0]['message']['content']
#
#             # emotion 번역
#             translated_emotion = translate_to_korean(emotion)
#
#             # 일기 저장
#             unique_diary_id = f"{timezone.now().strftime('%Y%m%d%H%M%S')}{diarytitle}"
#             diary_entry = AiwriteModel.objects.create(
#                 unique_diary_id=unique_diary_id,
#                 user_email=user_email,
#                 diarytitle=diarytitle,
#                 place=place,
#                 emotion=translated_emotion,
#                 withfriend=withfriend,
#                 content=GPT3content,
#             )
#             diary_entry.save()
#
#             # 대표 이미지 처리
#             if representative_image:
#                 image_model = ImageModel(is_representative=True)
#                 image_model.save_image(Image.open(representative_image))
#                 image_model.save()
#                 diary_entry.representative_image = image_model
#                 diary_entry.save()
#
#             # 추가 이미지 처리
#             images = request.FILES.getlist('images')
#             for img in images:
#                 additional_image_model = ImageModel(is_representative=False)
#                 additional_image_model.save_image(Image.open(img))
#                 additional_image_model.save()
#                 diary_entry.images.add(additional_image_model)  # ManyToMany 관계 설정
#
#             return redirect('list_diary')
#         else:
#             return render(request, 'diaryapp/list_diary.html', {'form': form, 'image_form': image_form})
#
#     else:
#         form = DiaryForm()
#         image_form = ImageUploadForm()
#
#     return render(request, 'diaryapp/write_diary.html', {'form': form, 'image_form': image_form})


# 직접 일기 부분 작성
def write_diary(request):
    if request.method == 'POST':
        form = DiaryForm(request.POST, request.FILES)
        image_form = ImageUploadForm(request.POST, request.FILES)

        if form.is_valid() and image_form.is_valid():
            diarytitle = form.cleaned_data['diarytitle']
            place = form.cleaned_data['place']
            emotion = form.cleaned_data['emotion']
            withfriend = form.cleaned_data['withfriend']
            content = form.cleaned_data['content']

            # user_email = request.user.email if request.user.is_authenticated else None
            user_email = settings.DEFAULT_FROM_EMAIL

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
                content=content,
            )
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

            return redirect('list_diary')
        else:
            return render(request, 'diaryapp/write_diary.html', {'form': form, 'image_form': image_form})
    else:
        form = DiaryForm()
        image_form = ImageUploadForm()

    return render(request, 'diaryapp/write_diary.html', {'form': form, 'image_form': image_form})


# 블로그 글 리스트
def list_diary(request):
    # user_email = request.user.email if request.user.is_authenticated else None
    user_email = settings.DEFAULT_FROM_EMAIL
    diary_list = AiwriteModel.objects.all().order_by('-created_at')
    return render(request, 'diaryapp/list_diary.html', {'diary_list': diary_list})

# 일기 내용 확인
def detail_diary_by_id(request, unique_diary_id):
    # user_email = request.user.email if request.user.is_authenticated else None
    user_email = settings.DEFAULT_FROM_EMAIL
    diary = get_object_or_404(AiwriteModel, unique_diary_id=unique_diary_id)
    return render(request, 'diaryapp/detail_diary.html', {'diary': diary})

# 일기 내용 수정
def update_diary(request, unique_diary_id):
    diary = get_object_or_404(AiwriteModel, unique_diary_id=unique_diary_id)

    if request.method == 'POST':

        # emotion 번역
        diary.diarytitle = request.POST['diarytitle']
        diary.place = request.POST['place']
        diary.emotion = request.POST['emotion']
        diary.emotion = translate_to_korean(diary.emotion)
        diary.withfriend = request.POST['withfriend']
        diary.content = request.POST['content']

        # user_email = request.user.email if request.user.is_authenticated else None
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

# 일기 내용 삭제
def delete_diary(request, unique_diary_id):
    # user_email = request.user.email if request.user.is_authenticated else None
    user_email = settings.DEFAULT_FROM_EMAIL
    diary = get_object_or_404(AiwriteModel, unique_diary_id=unique_diary_id)
    if request.method == 'POST':
        diary.delete()
        return redirect('list_diary')
    return redirect('list_diary')