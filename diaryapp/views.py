# diaryapp/views.py
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

def image_detail(request, pk):
    image_model = ImageModel.objects.get(pk=pk)
    image_data = base64.b64decode(image_model.image_file)
    return HttpResponse(image_data, content_type="image/png")

def generate_dynamic_descriptions():
    descriptions = [
        "dog", "park", "cat", "sunset", "ocean",
        "street", "landscape", "mountain", "tree", "flow", "friends", "picnic",
        "bridge", "sky", "market", "fruits", "vegetables",
        "beach", "sea", "coffee", " books", "cafe", "family", " zoo",
        "couple", " park", "castle", "flower", "street", "village", "bridge"
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
            # video_file = request.FILES.get('video_file')
            # sticker_file = request.FILES.get('sticker_file')

            user_email = settings.DEFAULT_FROM_EMAIL
            # user_email = request.user.email  # if request.user.is_authenticated else None

            # emotion, place 번역
            translated_emotion = translate_to_English(emotion)
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

            # 프롬프트 생성
            # prompt = (f"I recently visited {translated_place}. "
            #           f"During my trip, I felt a strong sense of {translated_emotion}. "
            #           f"One of the notable experiences was {best_description}. "
            #           f"Here are the details of my trip to {translated_place}, focusing on my experiences and feelings:"
            #           f"\n\n"
            #           f"Day 1: I arrived at {translated_place} and was immediately struck by {best_description}. "
            #           f"The place was exactly what I imagined, filled with {translated_emotion}. "
            #           f"\n\n"
            #           f"Day 2: I explored more of {translated_place}. The highlight of the day was experiencing {best_description}. "
            #           f"It made me feel {translated_emotion}, and I was deeply moved by the atmosphere."
            #           f"\n\n"
            #           f"Day 3: On the last day of my trip, I reflected on my experiences. The {best_description} stood out the most. "
            #           f"Overall, my visit to {translated_place} was filled with {translated_emotion}, making it a memorable trip."
            #           f"\n\n"
            #           f"This was my travel diary from {translated_place}. Please expand on this by adding specific details, interactions, and personal reflections to make it feel like a natural and vivid diary entry."
            #           f"It must include {translated_place},{translated_emotion} and {best_description}"
            #           f"Please write a travel diary based on the information."
            #           f"Think of it as your own experience and write it down"
            #           f"I want you to write it. Don't ask me for any more information "
            #           )
            prompt = (f"Please draft my travel diary based on this information."
                      f"I recently visited {translated_place} in korea. "
                      f"During my trip, I felt a strong sense of {translated_emotion}. "
                      f"One of the notable experiences was {best_description}. "
                      f"It must include {translated_place},{translated_emotion} and {best_description}"
                      )

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

            # 일기 저장
            unique_diary_id = f"{timezone.now().strftime('%Y%m%d%H%M%S')}{diarytitle}"
            diary_entry = AiwriteModel.objects.create(
                unique_diary_id=unique_diary_id,
                user_email=user_email,
                diarytitle=diarytitle,
                place=place,
                emotion=emotion,
                withfriend=withfriend,
                content=translated_text,
            )
            diary_entry.save()

            # 대표 이미지 처리
            # representative_image = request.FILES.get('image_file')
            if representative_image:
                image_model = ImageModel(is_representative=True)
                image_model.save_image(Image.open(representative_image))
                image_model.save()
                diary_entry.representative_image = image_model
                diary_entry.save()
                diary_entry.images.add(image_model)  # ManyToMany 관계 설정

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

            user_email = settings.DEFAULT_FROM_EMAIL

            # 일기 저장
            unique_diary_id = f"{timezone.now().strftime('%Y%m%d%H%M%S')}{diarytitle}"
            diary_entry = AiwriteModel.objects.create(
                unique_diary_id=unique_diary_id,
                user_email=user_email,
                diarytitle=diarytitle,
                place=place,
                emotion=emotion,
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
                diary_entry.images.add(image_model)  # ManyToMany 관계 설정

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
    # user_email = request.user.email #if request.user.is_authenticated else None
    user_email = settings.DEFAULT_FROM_EMAIL
    diary_list = AiwriteModel.objects.all().order_by('-created_at')
    return render(request, 'diaryapp/list_diary.html', {'diary_list': diary_list})

# 일기 내용 확인
def detail_diary_by_id(request, unique_diary_id):
    # user_email = request.user.email #if request.user.is_authenticated else None
    user_email = settings.DEFAULT_FROM_EMAIL
    diary = get_object_or_404(AiwriteModel, unique_diary_id=unique_diary_id)
    return render(request, 'diaryapp/detail_diary.html', {'diary': diary})

# 일기 내용 수정
def update_diary(request, unique_diary_id):
    diary = get_object_or_404(AiwriteModel, unique_diary_id=unique_diary_id)
    image_instances = ImageModel.objects.filter(diary=diary).all()

    if request.method == 'POST':
        form = DiaryForm(request.POST, request.FILES, instance=diary)

        if form.is_valid():
            form.save()

            # 대표 이미지 처리
            representative_image = request.FILES.get('image_file')
            if representative_image:
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
                diary.images.add(additional_image_model)

            # 일기 상세 페이지로 리디렉션
            return redirect(reverse('detail_diary_by_id', kwargs={'unique_diary_id': unique_diary_id}))
    else:
        form = DiaryForm(instance=diary)
        image_form = ImageUploadForm()  # 이미지 단일 폼 객체 생성

    return render(request, 'diaryapp/update_diary.html', {'form': form, 'image_form': image_form})
# 일기 내용 삭제
def delete_diary(request, unique_diary_id):
  diary = get_object_or_404(AiwriteModel, unique_diary_id=unique_diary_id)
  if request.method == 'POST':
      diary.delete()
      return redirect('list_diary')

  return redirect('list_diary')