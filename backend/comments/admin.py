from django.contrib import admin
from .models import Comment, Attachment


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """
    Админка для комментариев.
    Нужна в основном для отладки и для демонстрации данных проверяющему.
    """
    list_display = ('id', 'user_name', 'email', 'parent', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user_name', 'email', 'text')
    readonly_fields = ('created_at', 'ip_address', 'user_agent')
    date_hierarchy = 'created_at'


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    """Админка для вложений: картинок и текстовых файлов."""
    list_display = ('id', 'comment', 'file_type', 'original_name', 'uploaded_at')
    list_filter = ('file_type', 'uploaded_at')
    readonly_fields = ('uploaded_at',)