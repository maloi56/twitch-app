from django.contrib import admin

from users.models import UserInfo, Leaderboard, LeaderboardMembers


@admin.register(UserInfo)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'user',)
    readonly_fields = ('user',)


@admin.register(Leaderboard)
class LeaderboardAdmin(admin.ModelAdmin):
    list_display = ('id', 'channel', 'created')