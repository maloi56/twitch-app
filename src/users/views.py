from django.shortcuts import render
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet
from users.permissions import IsOwner
from rest_framework import generics, mixins
from users.models import Leaderboard, BotSettings
from users.serializers import LeaderboardSerializer, BotSettingsSerializer, LeaderboardSecretSerializer


class LeaderBoardModalViewSet(mixins.RetrieveModelMixin, GenericViewSet):
    serializer_class = LeaderboardSerializer
    queryset = Leaderboard.objects.all()
    permission_classes = (IsOwner,)
    lookup_field = 'channel__username'


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


def oauth(request):
    return render(request, 'oauth.html')


def test(request):
    return render(request, 'test.html')
