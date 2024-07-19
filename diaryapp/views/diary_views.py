from django.shortcuts import render

def viewDiary(request):
    return render(request, 'diaryapp/diary.html')



