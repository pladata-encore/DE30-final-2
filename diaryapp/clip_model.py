import open_clip
from googletrans import Translator

# 전역 변수로 모델과 전처리기 설정
clip_model = None
preprocess = None

# def load_model(model_name='ViT-B-32'):
#     global clip_model, preprocess
#     model_info = open_clip.create_model_and_transforms(model_name, pretrained='openai')
#     clip_model = model_info[0]
#     preprocess = model_info[1]
#
# # 기본 모델을 'ViT-B-32'로 로드
# load_model('ViT-B-32')
def load_model(model_name='RN50'):
    global clip_model, preprocess
    model_info = open_clip.create_model_and_transforms(model_name, pretrained='openai')
    clip_model = model_info[0]
    preprocess = model_info[1]

# 더 작은 모델을 로드
load_model('RN50')
