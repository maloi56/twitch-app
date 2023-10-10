import asyncio

from channels.db import database_sync_to_async
from djangochannelsrestframework.generics import GenericAsyncAPIConsumer
from djangochannelsrestframework.observer.generics import (
    ObserverModelInstanceMixin, action)

from users.models import Leaderboard, LeaderboardMembers
from users.serializers import LeaderboardMembersSerializer


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
        return await self.send_json(content={'Error message': kwargs['message']}, close=True)

    @action()
    async def join_room(self, **kwargs):
        if not await self.validate_leaderboard():
            return await self.server_close(message='No such leaderboard')

        await self.send_json(content={'message': 'Got leaderboard widget'})
        self.schedule = asyncio.create_task(self.run_schedule())

    @action()
    async def send_message(self, **kwargs):
        return await self.send_json(content={'leaderboard': await self.get_ser_leaderboard()})

    async def validate_leaderboard(self):
        try:
            self.secret = (dict((x.split('=') for x in self.scope['query_string'].decode().split("&")))). \
                get('secret', None)
            return True if await self.get_leaderboard(self.secret) else False
        except Exception as e:
            print(e)
            return False

    async def run_schedule(self):
        while True:
            await self.get_leaderboard(self.secret)
            await self.send_message()
            await asyncio.sleep(15)

    @database_sync_to_async
    def get_leaderboard(self, secret):
        if self.leaderboard_settings is None:
            try:
                self.leaderboard_settings = Leaderboard.objects.filter(secret=secret).first()
            except Exception as e:
                print(e)
                return None

        self.leaderboard = (
            LeaderboardMembers.objects
            .filter(leaderboard=self.leaderboard_settings)
            .order_by('-points')
            .all().exclude(nickname=self.leaderboard_settings.channel.username)
            [:self.leaderboard_settings.widget_count]
        )

        return True

    @database_sync_to_async
    def get_ser_leaderboard(self):
        try:
            return LeaderboardMembersSerializer(self.leaderboard, many=True).data
        except Exception as e:
            asyncio.run(self.server_close(message=f'Exception inside getting serialized data. {str(e)}'))
            raise e
