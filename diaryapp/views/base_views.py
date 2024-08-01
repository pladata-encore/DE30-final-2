from django.shortcuts import render

# Bootstrap 테마 예시 페이지
def viewIndex(request):
    return render(request, 'diaryapp/index.html')
def viewElements(request):
    return render(request, 'diaryapp/elements.html')
def viewGeneric(request):
    return render(request, 'diaryapp/generic.html')