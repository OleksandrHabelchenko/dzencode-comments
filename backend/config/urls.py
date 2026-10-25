from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # Все API-маршруты живут под префиксом /api/,
    # чтобы не пересекаться с фронтендом
    path('api/comments/', include('comments.urls')),
]

# В режиме разработки Django сам раздаёт загруженные файлы.
# В продакшене это будет делать nginx — он справляется с этим быстрее.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)