from django.urls import path

from websockets.chat.consumers import RoomConsumer
from websockets.widget.consumers import Widget


websocket_urlpatterns = [
    # path("ws/", consumers.UserConsumer.as_asgi()),
    path('ws/twitch/', RoomConsumer.as_asgi()),
    path('ws/leaderboard/', Widget.as_asgi()),
]