from django.shortcuts import render

# Create your views here.
from django.shortcuts import render

# def index(request):
#     return render(request, 'app/diary.html')
from django.shortcuts import render, get_object_or_404, redirect
from .models import YourModel
from .forms import YourModelForm
def index(request):
    objects = YourModel.objects.all()
    return render(request, 'app/index.html', {'objects': objects})

def detail(request, id):
    try:
        object = YourModel.objects.get(pk=id)
    except YourModel.DoesNotExist:
        return render(request, 'app/detail.html', {'error_message': "No YourModel matches the given query."})
    return render(request, 'app/detail.html', {'object': object})

def your_model_create(request):
    if request.method == 'POST':
        form = YourModelForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('index')  # 저장 후 이동할 URL 이름 지정
    else:
        form = YourModelForm()
    return render(request, 'app/your_form.html', {'form': form})


def your_form_view(request):
    if request.method == 'POST':
        form = YourModelForm(request.POST)
        if form.is_valid():
            form.save()
            # 저장이 성공적으로 이루어졌을 때의 처리
    else:
        form = YourModelForm()

    return render(request, 'app/your_form.html', {'form': form})