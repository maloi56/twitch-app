import asyncio
import json

from channels.db import database_sync_to_async
from djangochannelsrestframework.generics import GenericAsyncAPIConsumer
from djangochannelsrestframework.observer.generics import (ObserverModelInstanceMixin, action)
from django.contrib.auth.models import AnonymousUser
from social_django.models import UserSocialAuth

from twitch_bot.main import Bot


class RoomConsumer(ObserverModelInstanceMixin, GenericAsyncAPIConsumer):
    bot = None
    token = None
    channel = None

    async def disconnect(self, code):
        if self.bot is not None:
            await self.bot.close()
        return super().disconnect(code)

    @action()
    async def join_room(self, **kwargs):
        if isinstance(self.scope['user'], AnonymousUser):
            return await self.send(text_data='Access token is not valid. Connection has closed', close=True)
        self.channel = self.scope['user'].username
        self.token = await self.get_access_token(self.channel)
        if self.bot is None:
            self.bot = Bot(token=self.token, initial_channels=[self.channel], send_message=self.send_message)
            asyncio.create_task(self.bot.start())
        print(f'channel: {self.channel}, token: {self.token} is running now')

    @action()
    async def send_message(self, message, **kwargs):
        await self.send_json(content=json.dumps({'name': message.channel.name, 'message': message.content}))

    @database_sync_to_async
    def get_access_token(self, channel):
        return json.loads(UserSocialAuth.objects.filter(user__username=channel).last().extra_data).get('access_token')
