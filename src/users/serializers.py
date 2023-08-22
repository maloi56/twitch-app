import json
from rest_framework import serializers

from social_django.models import UserSocialAuth
from users.models import Leaderboard, User


class LeaderboardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Leaderboard
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ["id", "username", "email", "password"]
        extra_kwargs = {'password': {'write_only': True}}
    

class UserSocialAuthSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSocialAuth
        fields = '__all__'
        twitch_token = serializers.SerializerMethodField()
        user=UserSerializer()

    def get_twitch_access_token(self):
        return json.loads(UserSocialAuth.objects.filter(user=self.user).last().extra_data).get('access_token')