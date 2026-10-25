from django.urls import path

from .views import CommentListCreateView, CommentThreadView, CaptchaView

# Пространство имён приложения: позволяет ссылаться на маршруты
# как 'comments:list', не конфликтуя с другими приложениями
app_name = 'comments'

urlpatterns = [
    path('', CommentListCreateView.as_view(), name='list-create'),
    # Маршрут капчи идёт перед <int:pk>: так очевиднее,
    # что конкретный адрес проверяется раньше шаблона с параметром
    path('captcha/', CaptchaView.as_view(), name='captcha'),
    path('<int:pk>/', CommentThreadView.as_view(), name='thread'),
]