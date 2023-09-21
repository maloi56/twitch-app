from django.core.cache import cache
from django.shortcuts import render
from rest_framework.viewsets import GenericViewSet, ModelViewSet
from users.permissions import IsOwner
from rest_framework import generics, mixins
from rest_framework.pagination import PageNumberPagination
from users.models import Leaderboard, BotSettings, LeaderboardMembers
from users.serializers import LeaderboardSerializer, BotSettingsSerializer, LeaderboardSecretSerializer, \
    LeaderboardMembersSerializer


class CustomPagination(PageNumberPagination):
    page_size = 10
    page_query_param = 'page'
    max_page_size = 1000


class LeaderBoardMembersModalViewSet(mixins.ListModelMixin, GenericViewSet):
    serializer_class = LeaderboardMembersSerializer
    queryset = LeaderboardMembers.objects.all()
    permission_classes = (IsOwner,)
    pagination_class = CustomPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        channel = self.request.query_params.get('channel', None)
        return queryset.filter(leaderboard__channel__username=channel).order_by('-points').exclude(nickname=channel)


class LeaderBoardModalViewSet(mixins.RetrieveModelMixin,
                              mixins.UpdateModelMixin,
                              GenericViewSet):
    serializer_class = LeaderboardSerializer
    queryset = Leaderboard.objects.all()
    permission_classes = (IsOwner,)
    lookup_field = 'channel__username'

    def get_object(self):
        key = f'leaderboard_settings_{self.kwargs[self.lookup_field]}'
        obj = cache.get(key)
        if not obj:
            obj = super().get_object()
            cache.set(key, obj, None)
        return obj

    def update(self, request, *args, **kwargs):
        key = f'leaderboard_settings_{self.kwargs[self.lookup_field]}'
        response = super().update(request, *args, **kwargs)
        cache.delete(key)
        return response


class LeaderboardSecret(mixins.RetrieveModelMixin, GenericViewSet):
    serializer_class = LeaderboardSecretSerializer
    queryset = Leaderboard.objects.all()
    permission_classes = (IsOwner,)
    lookup_field = 'channel__username'

    def get_object(self):
        obj = super().get_object()
        if self.request.query_params.get('new', False) == '1' or obj.secret is None:
            obj.secret = obj.update_secret()
        return obj


class BotSettingsViewSet(mixins.RetrieveModelMixin,
                         mixins.UpdateModelMixin,
                         GenericViewSet):
    serializer_class = BotSettingsSerializer
    queryset = BotSettings.objects.all()
    permission_classes = (IsOwner,)
    lookup_field = 'user__username'

    def get_object(self):
        key = f'bot_settings_{self.kwargs[self.lookup_field]}'
        obj = cache.get(key)
        if not obj:
            obj = super().get_object()
            cache.set(key, obj, None)
        return obj

    def update(self, request, *args, **kwargs):
        key = f'bot_settings_{self.kwargs[self.lookup_field]}'
        response = super().update(request, *args, **kwargs)
        cache.delete(key)
        return response


def oauth(request):
    return render(request, 'oauth.html')


def test(request):
    return render(request, 'test.html')
