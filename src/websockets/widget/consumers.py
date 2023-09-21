import asyncio

from channels.db import database_sync_to_async
from djangochannelsrestframework.generics import GenericAsyncAPIConsumer
from djangochannelsrestframework.observer.generics import (ObserverModelInstanceMixin, action)
from users.models import Leaderboard, LeaderboardMembers
from users.serializers import LeaderboardSerializer, LeaderboardMembersSerializer


class Widget(ObserverModelInstanceMixin, GenericAsyncAPIConsumer):
    leaderboard = None
    leaderboard_settings = None
    secret = None
    schedule = None

    async def disconnect(self, code):
        if self.schedule:
            self.schedule.cancel()
        return super().disconnect(code)

    @action()
    async def server_close(self, **kwargs):
        return await self.close()

    @action()
    async def join_room(self, **kwargs):
        if not await self.validate_leaderboard():
            return await self.send_json(content={'message': 'No such leaderboard'}, close=True)
        await self.send_json(content={'message': f'Got leaderboard widget'})

        self.schedule = asyncio.create_task(self.run_schedule())

    @action()
    async def send_message(self, **kwargs):
        return await self.send_json(content={'leaderboard': await self.get_ser_leaderboard()})

    async def validate_leaderboard(self):
        try:
            self.secret = (dict((x.split('=') for x in self.scope['query_string'].decode().split("&")))). \
                get('secret', None)

            await self.get_leaderboard(self.secret)
            return True
        except:
            return False

    # async def create_schedule(self):
    #     interval, created = IntervalSchedule.objects.get_or_create(every=10, period='seconds')
    #     leaderboard = await self.get_ser_leaderboard()
    #     PeriodicTask.objects.create(
    #         name=f'send leaderboard info for {self.secret}',
    #         task='repeat_order_make',
    #         interval=interval,
    #         args=leaderboard,
    #         start_time=timezone.now(),
    #     )
    async def run_schedule(self):
        while True:
            await self.send_message()
            await asyncio.sleep(15)

    @database_sync_to_async
    def get_leaderboard(self, secret):
        if self.leaderboard_settings is None:
            self.leaderboard_settings = Leaderboard.objects.filter(secret=secret).first()

        self.leaderboard = LeaderboardMembers.objects \
                               .filter(leaderboard=self.leaderboard_settings) \
                               .order_by('-points') \
                               .all() \
                               .exclude(nickname=self.leaderboard_settings.channel.username) \
            [:self.leaderboard_settings.widget_count]

        return self.leaderboard

    @database_sync_to_async
    def get_ser_leaderboard(self):
        return LeaderboardMembersSerializer(self.leaderboard, many=True).data
