import asyncio
from djangochannelsrestframework.generics import GenericAsyncAPIConsumer
from djangochannelsrestframework import mixins
from djangochannelsrestframework.observer.generics import (ObserverModelInstanceMixin, action)
from djangochannelsrestframework.observer import model_observer
from twitchio.ext import commands

from twitch_bot.main import Bot

class RoomConsumer(ObserverModelInstanceMixin, GenericAsyncAPIConsumer):
    token = 'a3ov4s7rurf8pivs9hd3h00zjz8qks' # accest token from twitch
    channel = 'malooooi'
    bot = None

    async def connect(self):
        await self.accept()
        if self.bot is None:
            self.bot = Bot(token=self.token, initial_channels=[self.channel])
            asyncio.create_task(self.bot.start())

    async def disconnect(self, close_code):
        # Здесь закройте соединение с Twitchio и освободите ресурсы
        bot = Bot(token=self.token, initial_channels=[self.channel])
        bot.close()
    async def receive(self, text_data):
        # Обработка входящих сообщений от клиента WebSocket
        pass

    async def twitch_event_handler(self, event):
        # Обработка событий от Twitchio бота
        pass
