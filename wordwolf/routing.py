from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/game/(?P<room_id>\w+)/$', consumers.WordWolfConsumer.as_asgi()),
]
    re_path(r'ws/lobby/$', consumers.LobbyConsumer.as_asgi()),
    re_path(r'ws/room/(?P<room_id>\w+)/$', consumers.RoomConsumer.as_asgi()),
]
