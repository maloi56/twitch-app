import json
from rest_framework import serializers

from social_django.models import UserSocialAuth
from users.models import Leaderboard, User, BotSettings, LeaderboardMembers


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username',)


class LeaderboardMembersSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaderboardMembers
        exclude = ('id', 'leaderboard',)
        read_only_fields = ('level', 'experience',)


class LeaderboardSerializer(serializers.ModelSerializer):
    channel = UserSerializer()
    leaderboard_members = LeaderboardMembersSerializer(many=True, read_only=True)

    class Meta:
        model = Leaderboard
        exclude = ['id']
        read_only_fields = ['channel']
        depth = 1


class BotSettingsSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    voice_status = serializers.ChoiceField(choices=BotSettings.VOICE_CHOICES, label='Выбор статуса', default=1)

    class Meta:
        model = BotSettings
        exclude = ['id']
        depth = 1
        read_only_fields = ['user']


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
        user = UserSerializer()

    def get_twitch_access_token(self):
        return json.loads(UserSocialAuth.objects.filter(user=self.user).last().extra_data).get('access_token')
