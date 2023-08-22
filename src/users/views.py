import json

from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from users.permissions import IsOwner

from social_django.models import UserSocialAuth

from users.models import Leaderboard
from users.serializers import LeaderboardSerializer

from twitch_bot.main import Bot


class LeaderBoardModalViewSet(ModelViewSet):
    serializer_class = LeaderboardSerializer
    permission_classes = (IsOwner,)
    queryset = Leaderboard.objects.all()

    def get_queryset(self):
        return self.queryset.filter(channel=self.request.user)


class TurnOnBot(APIView):
    permission_classes = (IsOwner,)

    def post(self, request, format=None):
        token = json.loads(UserSocialAuth.objects.filter(user=request.user).last().extra_data).get('access_token')
        print(request.user.username)
        channel = request.user.username
        bot = Bot(token=token, initial_channels=[channel])
        bot.run()
        return Response('HUUUI', status=200)


def oauth(request):
    return render(request, 'oauth.html')

def test(request):
    return render(request, 'test.html')
