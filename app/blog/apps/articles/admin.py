from django.contrib import admin
from .models import Comment,Article

class CommentAdmin(admin.ModelAdmin):
    list_display = ('comment_name', 'comment_email', 'article', 'is_question', 'status', 'comment_date')
    list_filter = ('is_question', 'status', 'comment_date')
    list_editable = ('status',)  # Можно менять статус прямо в списке
    search_fields = ('comment_name', 'comment_email', 'comment_text')
    readonly_fields = ('comment_date',)

    fieldsets = (
        (None, {
            'fields': ('article', 'comment_name', 'comment_email', 'comment_text')
        }),
        ('Вопрос', {
            'fields': ('is_question', 'status'),
        }),
        ('Служебное', {
            'fields': ('comment_date', 'icon_color'),
            'classes': ('collapse',),
        }),
    )


admin.site.register(Article)
admin.site.register(Comment, CommentAdmin)
