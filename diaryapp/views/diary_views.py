from django.shortcuts import render

'''다이어리 메인 화면'''
def viewDiary(request):
    return render(request, 'diaryapp/diary.html')

# def viewDiary(request, social_id):
#     user = get_object_or_404(User, writer=social_id)  # social_id를 통해 사용자 조회
#     diaries = Diary.objects.filter(writer=user)  # 작성자 필드를 통해 사용자의 다이어리 조회
#
#     context = {
#         'user': user,
#         'diaries': diaries,
#     }
#
#     return render(request, 'diaryapp/diary.html', context)



