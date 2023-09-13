from rest_framework.permissions import BasePermission
from users.models import Leaderboard


class IsOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Leaderboard):
            return obj.channel == request.user
        return obj.user == request.user

    def has_permission(self, request, view):
        username = request.user.username
        return request.query_params.get('channel', None) == username or \
            view.kwargs.get('channel__username', None) == username or \
            view.kwargs.get('user__username', None) == username
