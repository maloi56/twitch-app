from django.contrib import admin

from users.models import BotSettings, Leaderboard, LeaderboardMembers


@admin.register(BotSettings)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'user',)
    readonly_fields = ('user',)


class LeaderboardMembersInline(admin.StackedInline):
    model = LeaderboardMembers
    fields = ('nickname', 'points',)
    readonly_fields = ('nickname',)
    extra = 0


@admin.register(LeaderboardMembers)
class LeaderboardMembersAdmin(admin.ModelAdmin):
    model = LeaderboardMembers
    list_display = ('leaderboard', 'nickname', 'points',)
    fields = ('nickname', 'points',)
    readonly_fields = ('nickname',)


@admin.register(Leaderboard)
class LeaderboardAdmin(admin.ModelAdmin):
    list_display = ('id', 'channel',)
    fields = ('secret', 'points_per_msg', 'widget_count', 'points_name')
    # inlines = (LeaderboardMembersInline,)
