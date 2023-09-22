import asyncio
import json
import redis

from channels.db import database_sync_to_async
from django.core.cache import cache
from django.utils import timezone
from django_celery_beat.models import PeriodicTask, IntervalSchedule
from djangochannelsrestframework.generics import GenericAsyncAPIConsumer
from djangochannelsrestframework.observer.generics import (ObserverModelInstanceMixin, action)
from django.contrib.auth.models import AnonymousUser
from django.conf import settings
from social_django.models import UserSocialAuth
from users.models import BotSettings, Leaderboard, LeaderboardMembers
from twitch_bot.main import Bot

redis_client = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=2)


class RoomConsumer(ObserverModelInstanceMixin, GenericAsyncAPIConsumer):
    bot = None
    token = None
    channel = None
    settings = None
    leaderboard = None

    async def disconnect(self, code):
        if self.bot:
            await self.bot.close()
        await self.close_task()
        return super().disconnect(code)

    @action()
    async def server_close(self, **kwargs):
        return await self.close()

    @action()
    async def join_room(self, **kwargs):
        if not await self.validate_user():
            return await self.send_json(content={'message': 'Access token is not valid. Connection has closed'},
                                        close=True)
        await self.init_data()
        await self.init_celery_task()
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
            r_points = redis_client.hget(self.channel, nickname)
            points = int(r_points) if r_points else 0
            redis_client.hset(self.channel, nickname, points + self.leaderboard.points_per_msg)

            # instance, created = LeaderboardMembers.objects.get_or_create(leaderboard=self.leaderboard,
            #                                                              nickname=nickname)
            # instance.add_points(self.leaderboard.points_per_msg)

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

    @database_sync_to_async
    def init_celery_task(self):
        interval, created = IntervalSchedule.objects.get_or_create(every=15, period='seconds')
        per_task = PeriodicTask.objects.filter(name=f'update_points {self.channel}')
        if not per_task:
            PeriodicTask.objects.create(
                name=f'update_points {self.channel}',
                task='update_points',
                interval=interval,
                args=json.dumps([self.channel]),
                start_time=timezone.now(),
            )
        elif not per_task.first().enabled:
            per_task = per_task.first()
            per_task.enabled = True
            per_task.save()

    @database_sync_to_async
    def close_task(self):
        task = PeriodicTask.objects.filter(name=f'update_points {self.channel}')
        if task.exists():
            task = task.first()
            task.enabled = False
            task.save()
