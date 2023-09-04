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
        if self.bot is not None:
            await self.bot.close()
        return super().disconnect(code)

    @action()
    async def join_room(self, **kwargs):
        if isinstance(self.scope['user'], AnonymousUser):
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
        if self.settings.voice_status == BotSettings.ALL or \
                self.settings.voice_status == BotSettings.WITH_PREFIX and \
                message.content.split()[0] == '!' + self.settings.command:
            if await self.access_delay(self.channel, message.tags['display-name'], self.settings.delay):
                await self.send_json(content={'name': message.tags['display-name'],
                                              'message': message.content.removeprefix('!' + self.settings.command).strip()})
        await self.leaderboard_action(message)

    @database_sync_to_async
    def init_data(self):
        user = self.scope['user']
        self.channel = user.username
        self.token = json.loads(UserSocialAuth.objects.filter(user__username=self.channel).last().extra_data).get(
            'access_token')
        self.settings = BotSettings.objects.get(user=user)
        self.leaderboard = Leaderboard.objects.get(channel=user)

    @database_sync_to_async
    def leaderboard_action(self, message):
        instance, created = LeaderboardMembers.objects.get_or_create(leaderboard=self.leaderboard,
                                                                     nickname=message.tags['display-name'])
        instance.add_exp(15)

    @staticmethod
    async def access_delay(channel, nickname, delay):
        key = f'{channel}_{nickname}'
        if cache.get(key):
            return False
        else:
            cache.set(key, True, delay)
            return True
