from rest_framework import serializers
from django.conf import settings
from .models import MLMNode

User = settings.AUTH_USER_MODEL

class MLMNodeSerializer(serializers.ModelSerializer):
    user_display = serializers.CharField(source='user.username', read_only=True)
    left = serializers.SerializerMethodField()
    right = serializers.SerializerMethodField()

    class Meta:
        model = MLMNode
        fields = ['id', 'user', 'user_display', 'parent', 'position', 'active', 'created_at', 'left', 'right']

    def get_left(self, obj):
        left = obj.left_child()
        if not left:
            return None
        return {'id': left.id, 'user': str(left.user), 'active': left.active}

    def get_right(self, obj):
        right = obj.right_child()
        if not right:
            return None
        return {'id': right.id, 'user': str(right.user), 'active': right.active}
