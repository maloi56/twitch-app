from django.contrib import admin

from users.models import BotSettings, Leaderboard, LeaderboardMembers


@admin.register(BotSettings)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'user',)
    readonly_fields = ('user',)


class LeaderboardMembersInline(admin.StackedInline):
    model = LeaderboardMembers
    fields = ('nickname', 'level', 'experience',)
    readonly_fields = ('nickname',)
    extra = 0


@admin.register(Leaderboard)
class LeaderboardAdmin(admin.ModelAdmin):
    list_display = ('id', 'channel',)
    fields = ('secret',)
    inlines = (LeaderboardMembersInline,)
