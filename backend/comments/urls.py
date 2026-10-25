from django.urls import path

from .views import CommentListCreateView, CommentThreadView

# Пространство имён приложения: позволяет ссылаться на маршруты
# как 'comments:list', не конфликтуя с другими приложениями
app_name = 'comments'

urlpatterns = [
    path('', CommentListCreateView.as_view(), name='list-create'),
    path('<int:pk>/', CommentThreadView.as_view(), name='thread'),
]