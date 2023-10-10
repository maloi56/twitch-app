import asyncio
import json
import redis

from channels.db import database_sync_to_async
from django.core.cache import cache
from django.utils import timezone
from django_celery_beat.models import PeriodicTask, IntervalSchedule
from djangochannelsrestframework.generics import GenericAsyncAPIConsumer
from djangochannelsrestframework.observer.generics import action
from django.conf import settings
from social_django.models import UserSocialAuth
from users.models import BotSettings, Leaderboard, LeaderboardMembers
from twitch_bot.main import Bot
from users.serializers import LeaderboardMembersSerializer

redis_client = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=2)


class RoomConsumer(GenericAsyncAPIConsumer):
    bot = None
    token = None
    channel = None
    settings = None
    leaderboard = None
    leaderboard_members = None
    schedule_leaderboard= None

    __GREETING_MESSAGE = 'Successful connect to chat bot, Danya'

    async def disconnect(self, code):
        if self.bot:
            await self.bot.close()

        if self.schedule_leaderboard:
            self.schedule_leaderboard.cancel()

        await self.close_task()
        return super().disconnect(code)

    @action()
    async def server_close(self, **kwargs):
        return await self.send_json(content={'Error message': kwargs['message']}, close=True)

    @action()
    async def send_message(self, message, **kwargs):
        if await self.check_voice_status(message):
            msg = await self.validate_message(message)
            if msg:
                if await self.access_delay(message.tags['display-name']):
                    await self.send_json(content={'name': message.tags['display-name'], 'message': msg})
        await self.leaderboard_action(message)

    @database_sync_to_async
    def leaderboard_action(self, message):
        nickname = message.tags['display-name']
        if nickname != self.channel:
            r_points = redis_client.hget(self.channel, nickname)
            points = int(r_points) if r_points else 0
            redis_client.hset(self.channel, nickname, points + self.leaderboard.points_per_msg)

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
        return res if len(res) > 0 else None

    @database_sync_to_async
    def close_task(self):
        task = PeriodicTask.objects.filter(name=f'update_points {self.channel}')
        if task.exists():
            task = task.first()
            task.enabled = False
            task.save()

    @database_sync_to_async
    def init_data(self):
        try:
            secret = (dict((x.split('=') for x in self.scope['query_string'].decode().split("&")))).get('secret', None)

            self.leaderboard = Leaderboard.objects.get(secret=secret)
            self.channel = self.leaderboard.channel.username
            self.token = json.loads(UserSocialAuth.objects.filter(user__username=self.channel).last().extra_data). \
                get('access_token')
            self.settings = BotSettings.objects.get(user__username=self.channel)

        except Exception as e:
            asyncio.run(self.server_close(message=f'Exception inside init_data. {str(e)}'))
            raise e

        return True

    @database_sync_to_async
    def init_celery_task(self):
        try:
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
            return True
        except Exception as e:
            asyncio.run(self.server_close(message=f'Exception inside init_celery_task. {str(e)}'))
            raise e

    async def init_bot(self):
        if self.bot is None:
            self.bot = Bot(token=self.token, initial_channels=[self.channel], send_message=self.send_message, )
            task = asyncio.create_task(self.bot.start())
            task.add_done_callback(self.exception_handler)

    def exception_handler(self, task):
        if task.exception():
            self.bot = None
            return asyncio.create_task(self.server_close(message=str(task.exception())))

    # async def validate_user(self):
    #     return False if isinstance(self.scope['user'], AnonymousUser) else True

    @database_sync_to_async
    def get_leaderboard_members(self):
        self.leaderboard_members = LeaderboardMembers.objects \
                               .filter(leaderboard=self.leaderboard) \
                               .order_by('-points') \
                               .all() \
                               .exclude(nickname=self.channel) \
            [:self.leaderboard.widget_count]

        return True

    @database_sync_to_async
    def get_ser_leaderboard(self):
        try:
            return LeaderboardMembersSerializer(self.leaderboard_members, many=True).data
        except Exception as e:
            asyncio.run(self.server_close(message=f'Exception inside getting serialized data. {str(e)}'))
            raise e

    async def run_schedule_leaderboard(self):
        while True:
            await self.get_leaderboard_members()
            await self.send_leaderboard()
            await asyncio.sleep(15)

    @action()
    async def send_leaderboard(self, **kwargs):
        return await self.send_json(content={'leaderboard': await self.get_ser_leaderboard()})

    @action()
    async def join_room(self, **kwargs):
        # if not await self.validate_user():
        #     return await self.server_close(message='Access token is not valid. Connection has closed')

        if await self.init_data() and await self.init_celery_task():
            await self.init_bot()

            if self.leaderboard.active:
                self.schedule_leaderboard = asyncio.create_task(self.run_schedule_leaderboard())

            print(f'channel: {self.channel}, token: {self.token} is running now')
            return asyncio.create_task(self.send_json(content={'message': self.__GREETING_MESSAGE}))
