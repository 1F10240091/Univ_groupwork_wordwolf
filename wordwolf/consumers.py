import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Room, Member

class LobbyConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add('lobby', self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard('lobby', self.channel_name)

    async def room_update(self, event):
        await self.send(text_data=json.dumps(event))

class RoomConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        
        if self.scope["user"].is_authenticated:
            # Ensure member exists
            await self.add_member(self.scope["user"], self.room_id)
            
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_join',
                    'username': self.scope["user"].username
                }
            )
            
            # Notify lobby
            room_info = await self.get_room_info(self.room_id)
            if room_info:
                await self.channel_layer.group_send(
                    'lobby',
                    {
                        'type': 'room_update',
                        'action': 'update',
                        'room': room_info
                    }
                )

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        if self.scope["user"].is_authenticated:
            # Remove member and check for room deletion
            room_deleted = await self.remove_member(self.scope["user"], self.room_id)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_leave',
                    'username': self.scope["user"].username
                }
            )
            
            # Notify lobby
            if room_deleted:
                await self.channel_layer.group_send(
                    'lobby',
                    {
                        'type': 'room_update',
                        'action': 'delete',
                        'room_id': self.room_id
                    }
                )
            else:
                room_info = await self.get_room_info(self.room_id)
                if room_info:
                    await self.channel_layer.group_send(
                        'lobby',
                        {
                            'type': 'room_update',
                            'action': 'update',
                            'room': room_info
                        }
                    )

    async def user_join(self, event):
        username = event['username']
        await self.send(text_data=json.dumps({
            'type': 'user_join',
            'username': username
        }))

    async def user_leave(self, event):
        username = event['username']
        await self.send(text_data=json.dumps({
            'type': 'user_leave',
            'username': username
        }))

    @database_sync_to_async
    def add_member(self, user, room_id):
        try:
            room = Room.objects.get(id=room_id)
            Member.objects.get_or_create(user=user, room=room)
        except Room.DoesNotExist:
            pass

    @database_sync_to_async
    def remove_member(self, user, room_id):
        try:
            room = Room.objects.get(id=room_id)
            Member.objects.filter(user=user, room=room).delete()
            if room.members.count() == 0:
                room.delete()
                return True # Room deleted
            return False
        except Room.DoesNotExist:
            return False

    @database_sync_to_async
    def get_room_info(self, room_id):
        try:
            room = Room.objects.get(id=room_id)
            return {
                'id': room.id,
                'room_name': room.room_name,
                'member_count': room.members.count(),
                'max_user_num': room.max_user_num,
                'status': room.get_status_display(),
                'is_full': room.is_full,
                'created_at': room.created_at.strftime('%Y/%m/%d %H:%M')
            }
        except Room.DoesNotExist:
            return None
