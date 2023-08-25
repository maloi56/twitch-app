from django.shortcuts import render
from rest_framework.viewsets import GenericViewSet
from users.permissions import IsOwner
from rest_framework import generics, mixins
from users.models import Leaderboard, BotSettings
from users.serializers import LeaderboardSerializer, BotSettingsSerializer


class LeaderBoardModalViewSet(mixins.RetrieveModelMixin, GenericViewSet):
    serializer_class = LeaderboardSerializer
    queryset = Leaderboard.objects.all()
    permission_classes = (IsOwner,)
    lookup_field = 'channel__username'


class BotSettingsViewSet(mixins.RetrieveModelMixin,
                         mixins.UpdateModelMixin,
                         GenericViewSet):
    serializer_class = BotSettingsSerializer
    queryset = BotSettings.objects.all()
    permission_classes = (IsOwner,)
    lookup_field = 'user__username'


def oauth(request):
    return render(request, 'oauth.html')


def test(request):
    return render(request, 'test.html')
