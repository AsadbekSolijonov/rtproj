from django.contrib import admin
from chat.models import Message


@admin.register(Message)
class Message(admin.ModelAdmin):
    list_display = ['id', 'user', 'text', 'created_at']
