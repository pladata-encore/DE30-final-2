from django.test import TestCase

# Create your tests here.
from django.test import Client, TestCase
from django.urls import reverse
from .models import AiwriteModel

from django.test import Client, TestCase
from django.urls import reverse
from django.contrib.auth import authenticate, login
from .models import AiwriteModel

class DiaryTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.diary = AiwriteModel.objects.create(user_email='user1@example.com', diarytitle='Test Diary', content='Test Content')

    def test_view_diary(self):
        # 로그인하지 않은 상태에서 일기를 조회하는 요청을 보냅니다.
        response = self.client.get(reverse('detail_diary_by_id', args=[self.diary.unique_diary_id]))
        # HTTP 상태 코드를 확인합니다. 로그인하지 않은 사용자는 접근할 수 없으므로, 상태 코드는 302(리다이렉트)이어야 합니다.
        self.assertEqual(response.status_code, 302)

        # user1로 로그인합니다.
        user = authenticate(username='user1@example.com', password='password')
        login(self.client, user)

        # 로그인한 상태에서 자신이 작성한 일기를 조회하는 요청을 보냅니다.
        response = self.client.get(reverse('detail_diary_by_id', args=[self.diary.unique_diary_id]))
        # HTTP 상태 코드를 확인합니다. 로그인한 사용자는 자신이 작성한 일기를 볼 수 있으므로, 상태 코드는 200이어야 합니다.
        self.assertEqual(response.status_code, 200)
        # 사용된 템플릿을 확인합니다. 자신이 작성한 일기를 조회하는 경우 'diaryapp/detail_diary.html' 템플릿이 사용되어야 합니다.
        self.assertTemplateUsed(response, 'diaryapp/detail_diary.html')

        # user1로부터 로그아웃하고 user2로 로그인합니다.
        self.client.logout()
        user = authenticate(username='user2@example.com', password='password')
        login(self.client, user)

        # 로그인한 상태에서 다른 사용자가 작성한 일기를 조회하는 요청을 보냅니다.
        response = self.client.get(reverse('detail_diary_by_id', args=[self.diary.unique_diary_id]))
        # HTTP 상태 코드를 확인합니다. 로그인한 사용자는 다른 사용자가 작성한 일기를 볼 수 있으므로, 상태 코드는 200이어야 합니다.
        self.assertEqual(response.status_code, 200)
        # 사용된 템플릿을 확인합니다. 다른 사용자가 작성한 일기를 조회하는 경우 'diaryapp/detail_diary_otheruser.html' 템플릿이 사용되어야 합니다.
        self.assertTemplateUsed(response, 'diaryapp/detail_diary_otheruser.html')
