import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.utils.timezone import now
from django.contrib.auth.models import AnonymousUser
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware

from django.contrib.auth.models import User
from django.db import close_old_connections

from oauth2_provider.models import AccessToken

ALGORITHM = "HS256"


@database_sync_to_async
def get_user(token):
    try:
        payload = AccessToken.objects.filter(token=token).last()
        if payload is None:
            return AnonymousUser()
        print('payload', payload)
    except:
        print('no payload')
        return AnonymousUser()

    token_exp = payload.expires
    if token_exp < now():
        print("no date-time")
        return AnonymousUser()

    try:
        user = payload.user
        print('user', user)
    except User.DoesNotExist:
        print('no user')
        return AnonymousUser()

    return user


class TokenAuthMiddleware(BaseMiddleware):

    async def __call__(self, scope, receive, send):
        close_old_connections()
        try:
            token_key = (dict((x.split('=') for x in scope['query_string'].decode().split("&")))).get('token', None)
        except ValueError:
            token_key = None
        scope['user'] = await get_user(token_key)
        print('d2', scope['user'])
        return await super().__call__(scope, receive, send)


def JwtAuthMiddlewareStack(inner):
    return TokenAuthMiddleware(inner)
