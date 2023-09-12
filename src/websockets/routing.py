from django.urls import path

from websockets import RoomConsumer, Widget


websocket_urlpatterns = [
    # path("ws/", consumers.UserConsumer.as_asgi()),
    path('ws/twitch/', RoomConsumer.as_asgi()),
    path('ws/leaderboard/', Widget.as_asgi()),
]