from rest_framework import serializers

from users.models import Leaderboard


class LeaderboardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Leaderboard
        fields = '__all__'
