from django.core.cache import cache
from django.shortcuts import render
from rest_framework.mixins import (ListModelMixin, RetrieveModelMixin,
                                   UpdateModelMixin)
from rest_framework.pagination import PageNumberPagination
from rest_framework.viewsets import GenericViewSet

from users.mixins.custom_mixins import CachedObjectMixin
from users.models import BotSettings, Leaderboard, LeaderboardMembers
from users.permissions import IsOwner
from users.serializers import (BotSettingsSerializer,
                               LeaderboardMembersSerializer,
                               LeaderboardSecretSerializer,
                               LeaderboardSerializer)


class CustomPagination(PageNumberPagination):
    page_size = 10
    page_query_param = 'page'
    max_page_size = 1000


class LeaderBoardMembersModalViewSet(ListModelMixin, GenericViewSet):
    serializer_class = LeaderboardMembersSerializer
    queryset = LeaderboardMembers.objects.all()
    permission_classes = (IsOwner,)
    pagination_class = CustomPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        channel = self.request.query_params.get('channel', None)
        return queryset.filter(leaderboard__channel__username=channel).order_by('-points').exclude(nickname=channel)


class LeaderBoardModalViewSet(CachedObjectMixin, RetrieveModelMixin, UpdateModelMixin, GenericViewSet):

    serializer_class = LeaderboardSerializer
    queryset = Leaderboard.objects.all()
    permission_classes = (IsOwner,)
    lookup_field = 'channel__username'

    def update(self, request, *args, **kwargs):
        key = f'{self.__class__.__name__}_{self.kwargs[self.lookup_field]}'
        response = super().update(request, *args, **kwargs)
        cache.delete(key)
        return response


class LeaderboardSecret(CachedObjectMixin, RetrieveModelMixin, GenericViewSet):
    serializer_class = LeaderboardSecretSerializer
    queryset = Leaderboard.objects.all()
    permission_classes = (IsOwner,)
    lookup_field = 'channel__username'

    def get_object(self):
        obj = super().get_object()
        if self.request.query_params.get('new', False) == '1' or obj.secret is None:
            key = f'{self.__class__.__name__}_{self.kwargs[self.lookup_field]}'
            obj.secret = obj.update_secret()
            cache.set(key, obj, self.ONE_WEEK)
        return obj


class BotSettingsViewSet(CachedObjectMixin, RetrieveModelMixin, UpdateModelMixin, GenericViewSet):
    serializer_class = BotSettingsSerializer
    queryset = BotSettings.objects.all()
    permission_classes = (IsOwner,)
    lookup_field = 'user__username'

    def update(self, request, *args, **kwargs):
        key = f'{self.__class__.__name__}_{self.kwargs[self.lookup_field]}'
        response = super().update(request, *args, **kwargs)
        cache.delete(key)
        return response


def oauth(request):
    return render(request, 'oauth.html')


def test(request):
    return render(request, 'test.html')
