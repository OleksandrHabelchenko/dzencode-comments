from django.conf import settings

from django.conf.urls.static import static

from django.contrib import admin

from django.urls import path, include

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # Все API-маршруты живут под префиксом /api/,
    # чтобы не пересекаться с фронтендом
    path('api/comments/', include('comments.urls')),

    # Аутентификация по токенам:
    # token/         — вход по логину и паролю, выдаёт пару access + refresh
    # token/refresh/ — обновление access-токена по refresh-токену
    # token/verify/  — проверка, что токен ещё действителен
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
]

# В режиме разработки Django сам раздаёт загруженные файлы.
# В продакшене это будет делать nginx — он справляется с этим быстрее.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)