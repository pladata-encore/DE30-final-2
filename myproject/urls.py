import subprocess
import threading
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.urls import re_path
from django.conf.urls.static import static
from rest_framework.permissions import AllowAny
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from drf_yasg.generators import OpenAPISchemaGenerator



urlpatterns= [
    path('admin/', admin.site.urls),
    path('travel/', include('travel_recommend.urls')),
    path('jpages/', include('Jpage.urls', namespace='Jpage')),
    path('diary/', include('diaryapp.urls')),
    path('oauth/', include('oauth.urls')),  # oauth 애플리케이션의 URL 패턴을 포함
    path('users/', include('users.urls')),  # users 애플리케이션의 URL 패턴을 포함
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# 디버그일때 swagger api 실행
if settings.DEBUG:
    # Schemes HTTPS 버튼 추가
    class BothHttpAndHttpsSchemaGenerator(OpenAPISchemaGenerator):
        def get_schema(self, request=None, public=False):
            schema = super().get_schema(request, public)
            schema.schemes = ["http", "https"]
            return schema

    schema_view = get_schema_view(
        openapi.Info(
            title="Open API Swagger Test",
            default_version='v1',
            description="시스템 API Description",
            # reah_of_service="',
            # contact=openapi.Contact(name="test", email="test@test.test'),
            # license=openapi.License(name="Test License'),
        ),
        public=True,
        generator_class=BothHttpAndHttpsSchemaGenerator,
        permission_classes=(AllowAny,),
    )

    urlpatterns += [
        re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
        re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
        re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    ]