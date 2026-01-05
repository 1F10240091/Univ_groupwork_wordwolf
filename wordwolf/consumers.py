import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Room, ChatMessage, Member

class WordWolfConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'game_{self.room_id}'
        self.user = self.scope["user"]

        if self.user.is_authenticated:
            is_new_member = await self.join_room_member()
            await self.accept()
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)

            messages = await self.get_past_messages()
            await self.send(text_data=json.dumps({
                'type': 'chat_log',
                'messages': messages
            }))
            if is_new_member:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'member_joined',
                        'user_name': self.user.username
                    }
                )
        else:
            await self.close()

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.broadcast_member_list()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        await self.broadcast_member_list()

    async def receive(self, text_data):
        data = json.loads(text_data)

        if data['type'] == 'chat':
            message = data.get('message')
            user = self.scope["user"]
            if message:
                await self.save_chat_message(user, message)

                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_broadcast',
                        'message': message,
                        'sender_name': user.username
                    }
                )
    async def chat_broadcast(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message'],
            'sender_name': event['sender_name']
        }))
    async def broadcast_member_list(self):
        members = await self.get_current_members()
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'member_list_update',
                'members': members
            }
        )
    async def member_list_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'member_list',
            'members': event['members']
        }))

    @database_sync_to_async
    def join_room_member(self):
        room = Room.objects.get(id=self.room_id)
        
        # すでにこの部屋にこのユーザーがいれば取得、いなければ作成
        member, created = Member.objects.get_or_create(
            room=room,
            user=self.user
        )
        return created

    @database_sync_to_async
    def save_chat_message(self, user, message):
        try:
            room = Room.objects.get(id=self.room_id)
            ChatMessage.objects.create(
                room=room,
                user=user if user and not isinstance(user, str) else None,
                message=message,
                is_system=True if not user or isinstance(user, str) else False
            )
        except Room.DoesNotExist:
            print(f"Error: Room {self.room_id} not found.")
    
    async def member_joined(self, event):
        await self.send(text_data=json.dumps({
            'type': 'system_message',
            'message': f"{event['user_name']}さんが入室しました。"
        }))
        await self.save_chat_message(None, f"{event['user_name']}さんが入室しました。")
    
    @database_sync_to_async
    def get_past_messages(self):
        msgs = ChatMessage.objects.filter(room_id=self.room_id).order_by('timestamp')
        return [
            {
                'sender_name': m.user.username if m.user else "システム",
                'message': m.message,
                'is_system': m.is_system
            } for m in msgs
        ]
    @database_sync_to_async
    def get_current_members(self):
        members = Member.objects.filter(room_id=self.room_id)
        return [m.user.username for m in members]