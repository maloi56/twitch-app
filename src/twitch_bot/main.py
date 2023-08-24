from twitchio.ext import commands


class Bot(commands.Bot):

    def __init__(self, token, initial_channels, send_message):
        super().__init__(token=token, prefix='?', initial_channels=initial_channels)
        self.send_message = send_message

    async def event_ready(self):
        # Notify us when everything is ready!
        # We are logged in and ready to chat and use commands...
        print(f'Logged in as | {self.nick}')
        print(f'User id is | {self.user_id}')

    async def event_message(self, message):
        if message.echo:
            return
        await self.handle_commands(message)
        await self.send_message(message=message)

