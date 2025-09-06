from rest_framework import serializers
from .models import Message


class MessageSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.get_username", read_only=True)
    user_id = serializers.IntegerField(source="user.id", read_only=True)

    class Meta:
        model = Message
        fields = ["id", "username", "user_id", "text", "created_at"]
        read_only_fields = ["id", "created_at", "username", "user_id"]
