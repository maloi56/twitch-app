import asyncio
import json

from channels.db import database_sync_to_async
from djangochannelsrestframework.generics import GenericAsyncAPIConsumer
from djangochannelsrestframework.observer.generics import (ObserverModelInstanceMixin, action)
from users.models import Leaderboard
from users.serializers import LeaderboardSerializer


class Widget(ObserverModelInstanceMixin, GenericAsyncAPIConsumer):
    leaderboard = None
    secret = None
    schedule = None

    async def disconnect(self, code):
        self.schedule.cancel()
        return super().disconnect(code)

    @action()
    async def server_close(self, **kwargs):
        return await self.close()

    @action()
    async def join_room(self, **kwargs):
        if not await self.validate_leaderboard():
            return await self.send_json(content={'message': 'No such leaderboard'}, close=True)
        await self.send_json(content={'message': f'Got "ХЗ ПОЧЕму ТУт ОШИбКА" leaderboard'})

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
            await asyncio.sleep(5)

    @database_sync_to_async
    def get_leaderboard(self, secret):
        self.leaderboard = Leaderboard.objects.filter(secret=secret).first()
        return self.leaderboard

    @database_sync_to_async
    def get_ser_leaderboard(self):
        return LeaderboardSerializer(self.leaderboard).data
