import asyncio
import json

from channels.db import database_sync_to_async
from django.core.cache import cache
from djangochannelsrestframework.generics import GenericAsyncAPIConsumer
from djangochannelsrestframework.observer.generics import (ObserverModelInstanceMixin, action)
from django.contrib.auth.models import AnonymousUser
from social_django.models import UserSocialAuth
from users.models import BotSettings, Leaderboard, LeaderboardMembers
from twitch_bot.main import Bot


class RoomConsumer(ObserverModelInstanceMixin, GenericAsyncAPIConsumer):
    bot = None
    token = None
    channel = None
    settings = None
    leaderboard = None

    async def disconnect(self, code):
        if self.bot:
            await self.bot.close()
        return super().disconnect(code)

    @action()
    async def join_room(self, **kwargs):
        if not await self.validate_user():
            return await self.send_json(content={'message': 'Access token is not valid. Connection has closed'},
                                        close=True)
        await self.init_data()
        if self.bot is None:
            self.bot = Bot(token=self.token,
                           initial_channels=[self.channel],
                           send_message=self.send_message, )

            asyncio.create_task(self.bot.start())
            await self.send_json(content={'message': 'Successful connect to chat bot, Danya'})
        print(f'channel: {self.channel}, token: {self.token} is running now')

    @action()
    async def send_message(self, message, **kwargs):
        if await self.check_voice_status(message):
            msg = await self.validate_message(message)
            if msg:
                if await self.access_delay(message.tags['display-name']):
                    await self.send_json(content={'name': message.tags['display-name'], 'message': msg})
        await self.leaderboard_action(message)

    @database_sync_to_async
    def init_data(self):
        user = self.scope['user']
        self.channel = user.username
        self.token = json.loads(UserSocialAuth.objects.filter(user__username=self.channel).last().extra_data). \
            get('access_token')

        self.settings = BotSettings.objects.get(user=user)
        self.leaderboard = Leaderboard.objects.get(channel=user)

    @database_sync_to_async
    def leaderboard_action(self, message):
        nickname = message.tags['display-name']
        if nickname != self.channel:
            instance, created = LeaderboardMembers.objects.get_or_create(leaderboard=self.leaderboard,
                                                                         nickname=nickname)
            instance.add_points(self.leaderboard.points_per_msg)

    async def validate_user(self):
        return False if isinstance(self.scope['user'], AnonymousUser) else True

    async def access_delay(self, nickname):
        key = f'{self.channel}_{nickname}'
        if cache.get(key):
            return False
        else:
            cache.set(key, True, self.settings.delay)
            return True

    async def check_voice_status(self, message):
        return True if self.settings.voice_status == BotSettings.ALL or \
                       self.settings.voice_status == BotSettings.WITH_PREFIX and \
                       message.content.startswith('!' + self.settings.command) else False

    async def validate_message(self, message):
        res = message.content.removeprefix('!' + self.settings.command).strip()
        return res if len(res) > 0 else False
