from django.shortcuts import render, redirect
from django.http import HttpResponse

# Create your views here.
def viewDiary(request):
    return render(request, 'diary.html')


# Bootstrap 테마 예시 페이지
def viewIndex(request):
    return render(request, 'index.html')
def viewElements(request):
    return render(request, 'elements.html')
def viewGeneric(request):
    return render(request, 'generic.html')