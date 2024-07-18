import open_clip

# 전역 변수로 모델과 전처리기 설정
clip_model = None
preprocess = None

def load_model():
    global clip_model, preprocess
    model_info = open_clip.create_model_and_transforms('ViT-B-32', pretrained='openai')
    clip_model = model_info[0]
    preprocess = model_info[1]

load_model()
