"""
ASGI config for twitch project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from users.middleware import JwtAuthMiddlewareStack
# from oauth2_provider.contrib.rest_framework import OAuth2Authentication

from users import routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'twitch.settings')

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": JwtAuthMiddlewareStack(
        URLRouter(
            routing.websocket_urlpatterns
        )
    ),
})
