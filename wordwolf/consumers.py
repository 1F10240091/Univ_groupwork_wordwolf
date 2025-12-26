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

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        
        if self.scope["user"].is_authenticated:
            await self.add_member(self.scope["user"], self.room_id)
            
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_join',
                    'username': self.scope["user"].username
                }
            )
            
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

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')

        if message_type == 'start_game':
            if await self.is_host(self.scope["user"], self.room_id):
                # 3人以上かチェック
                member_count = await self.get_member_count(self.room_id)
                if member_count >= 3:
                    await self.start_game_logic(self.room_id)
                    
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'game_start',
                        }
                    )
        elif message_type == 'leave_room':
            await self.handle_leave_room()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        if self.scope["user"].is_authenticated:
            is_host_user = await self.is_host(self.scope["user"], self.room_id)
            
            room_deleted = await self.remove_member(self.scope["user"], self.room_id)

            if is_host_user and not room_deleted:

                await self.delete_room_force(self.room_id)
                room_deleted = True
                
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'room_dissolved',
                    }
                )

            if not room_deleted:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'user_leave',
                        'username': self.scope["user"].username
                    }
                )


            if room_deleted:
                await self.channel_layer.group_send(
                    'lobby',
                    {'type': 'room_update', 'action': 'delete', 'room_id': self.room_id}
                )
            else:
                room_info = await self.get_room_info(self.room_id)
                if room_info:
                    await self.channel_layer.group_send(
                        'lobby',
                        {'type': 'room_update', 'action': 'update', 'room': room_info}
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
    
    async def game_start(self, event):
        await self.send(text_data=json.dumps({
            'type': 'game_start'
        }))

    async def room_dissolved(self, event):
        await self.send(text_data=json.dumps({
            'type': 'room_dissolved'
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
                return True
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
                'status': room.get_status_display(),
                'created_at': room.created_at.strftime('%Y/%m/%d %H:%M')
            }
        except Room.DoesNotExist:
            return None

    @database_sync_to_async
    def get_member_count(self, room_id):
        try:
            room = Room.objects.get(id=room_id)
            return room.members.count()
        except Room.DoesNotExist:
            return 0

    @database_sync_to_async
    def is_host(self, user, room_id):
        try:
            room = Room.objects.get(id=room_id)
            return room.host == user
        except Room.DoesNotExist:
            return False

    @database_sync_to_async
    def start_game_logic(self, room_id):
        try:
            room = Room.objects.get(id=room_id)
            room.status = Room.Status.PLAYING
            room.save()
            # ここで役職割り振りなどの処理を行う（後ほど実装）
        except Room.DoesNotExist:
            pass

    @database_sync_to_async
    def delete_room_force(self, room_id):
        try:
            Room.objects.get(id=room_id).delete()
        except Room.DoesNotExist:
            pass

    async def handle_leave_room(self):
        user = self.scope["user"]
        if not user.is_authenticated:
            return

        is_host_user = await self.is_host(user, self.room_id)
        
        if is_host_user:
            await self.delete_room_force(self.room_id)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'room_dissolved',
                }
            )
        else:
            await self.remove_member(user, self.room_id)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_leave',
                    'username': user.username
                }
            )
            # 自分自身に退出完了を通知
            await self.send(text_data=json.dumps({
                'type': 'leave_success'
            }))