import json
import random
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Room, Member, WordSet

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
            
            # ロビー一覧を更新
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
            
            # 既に参加しているメンバーに通知
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_join',
                    'username': self.scope["user"].username
                }
            )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')
        user = self.scope["user"]

        if message_type == 'start_game':
            if await self.is_host(user, self.room_id):
                member_count = await self.get_member_count(self.room_id)
                # テスト用に1人でも開始できるようにするか、本番通り3人以上にするか
                if member_count >= 1: # デバッグ用に緩和中。本番は3
                    if await self.start_game_logic(self.room_id):
                        await self.channel_layer.group_send(
                            self.room_group_name,
                            {'type': 'game_start'}
                        )

        elif message_type == 'leave_room':
            await self.handle_leave_room()

        elif message_type == 'confirm_start':
            await self.confirm_user(user, self.room_id)
            
            status = await self.get_confirmation_status(self.room_id)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'confirmation_update',
                    'confirmed_count': status['confirmed'],
                    'total_count': status['total']
                }
            )
            
            if status['confirmed'] == status['total'] and status['total'] > 0:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {'type': 'start_discussion'}
                )

        # --- 以下追加機能 ---
        
        elif message_type == 'chat_message':
            message = data.get('message')
            if message:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'username': user.username,
                        'message': message
                    }
                )

        elif message_type == 'request_game_info':
            # クライアントがゲーム画面を開いたときに自分の役職やお題を要求する
            game_info = await self.get_player_game_info(user, self.room_id)
            if game_info:
                await self.send(text_data=json.dumps({
                    'type': 'game_info',
                    'data': game_info
                }))

        elif message_type == 'vote':
            target_name = data.get('target')
            if target_name:
                all_voted = await self.register_vote(user, self.room_id, target_name)
                # 投票完了通知（誰が投票したか）
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'vote_update',
                        'username': user.username
                    }
                )
                
                if all_voted:
                    results = await self.calculate_results(self.room_id)
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'game_result',
                            'results': results
                        }
                    )

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        # ゲーム中の切断は複雑なので、今回は待機中のみ退出処理をする簡易実装とします
        # または handle_leave_room と同様のロジックを入れる

    # --- Event Handlers ---

    async def user_join(self, event):
        await self.send(text_data=json.dumps(event))

    async def user_leave(self, event):
        await self.send(text_data=json.dumps(event))
    
    async def game_start(self, event):
        await self.send(text_data=json.dumps(event))

    async def room_dissolved(self, event):
        await self.send(text_data=json.dumps(event))

    async def confirmation_update(self, event):
        await self.send(text_data=json.dumps(event))

    async def start_discussion(self, event):
        await self.send(text_data=json.dumps(event))

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'username': event['username'],
            'message': event['message']
        }))

    async def vote_update(self, event):
        await self.send(text_data=json.dumps(event))

    async def game_result(self, event):
        await self.send(text_data=json.dumps(event))

    # --- DB Operations ---

    @database_sync_to_async
    def add_member(self, user, room_id):
        try:
            room = Room.objects.get(id=room_id)
            # ゲーム中なら再接続のみ許可、新規参加は不可などの制御が必要だが、ここでは簡易化
            Member.objects.get_or_create(user=user, room=room)
        except Room.DoesNotExist:
            pass

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
            if room.status == Room.Status.PLAYING:
                return False

            # 1. お題の決定
            if room.category and room.category != 'all':
                wordsets = list(WordSet.objects.filter(category=room.category))
            else:
                wordsets = list(WordSet.objects.all())
            
            if not wordsets:
                # お題がない場合のフォールバック（適当なダミーデータなど）
                # ここではエラー回避のため処理中断
                return False
                
            selected_wordset = random.choice(wordsets)
            room.word_set = selected_wordset
            room.status = Room.Status.PLAYING
            room.save()

            # 2. 役職の割り振り (1人が人狼)
            members = list(room.members.all())
            if not members:
                return False
                
            random.shuffle(members)
            wolf = members[0]
            
            for member in members:
                if member == wolf:
                    member.role = Member.Role.WOLF
                    member.word = selected_wordset.wolf_word
                else:
                    member.role = Member.Role.CITIZEN
                    member.word = selected_wordset.main_word
                # 前回の投票などをリセット
                member.vote_target = None
                member.is_confirmed = False
                member.save()
            
            return True
        except Exception as e:
            print(f"Error in start_game_logic: {e}")
            return False

    @database_sync_to_async
    def get_player_game_info(self, user, room_id):
        try:
            room = Room.objects.get(id=room_id)
            member = Member.objects.get(user=user, room=room)
            
            # 全プレイヤー名のリスト
            all_members = [m.user.username for m in room.members.all()]
            
            return {
                'my_word': member.word,
                'role': member.role, # クライアント側で表示するかはJS次第（通常は隠す）
                'discussion_time': room.discussion_time,
                'members': all_members
            }
        except (Room.DoesNotExist, Member.DoesNotExist):
            return None

    @database_sync_to_async
    def register_vote(self, user, room_id, target_username):
        try:
            room = Room.objects.get(id=room_id)
            voter = Member.objects.get(user=user, room=room)
            target_user = Member.objects.get(room=room, user__username=target_username)
            
            voter.vote_target = target_user
            voter.save()
            
            # 全員投票したかチェック
            total_members = room.members.count()
            voted_count = room.members.filter(vote_target__isnull=False).count()
            
            return total_members == voted_count
        except Exception:
            return False

    @database_sync_to_async
    def calculate_results(self, room_id):
        room = Room.objects.get(id=room_id)
        members = list(room.members.all())
        
        # 投票の集計
        votes = {}
        for m in members:
            if m.vote_target:
                target_name = m.vote_target.user.username
                votes[target_name] = votes.get(target_name, 0) + 1
        
        # 最多得票者を探す
        max_votes = 0
        if votes:
            max_votes = max(votes.values())
        
        executed_names = [name for name, count in votes.items() if count == max_votes]
        
        # 人狼を探す
        wolves = [m for m in members if m.role == Member.Role.WOLF]
        wolf_names = [w.user.username for w in wolves]
        
        # 判定: 処刑された人の中に人狼がいれば市民の勝ち
        wolf_caught = False
        for executed in executed_names:
            if executed in wolf_names:
                wolf_caught = True
                break
        
        winner_role = '市民' if wolf_caught else '人狼'
        
        # 戦績更新
        for m in members:
            is_winner = False
            if wolf_caught and m.role == Member.Role.CITIZEN:
                is_winner = True
            elif not wolf_caught and m.role == Member.Role.WOLF:
                is_winner = True
            
            if is_winner:
                m.user.win_num += 1
            else:
                m.user.lose_num += 1
            m.user.save()
            
        room.status = Room.Status.FINISHED
        room.save()

        return {
            'winner': winner_role,
            'wolves': wolf_names,
            'votes': votes
        }
    
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
            await self.send(text_data=json.dumps({
                'type': 'leave_success'
            }))
            
            # ロビーの更新
            room_info = await self.get_room_info(self.room_id)
            if room_info:
                await self.channel_layer.group_send(
                    'lobby',
                    {'type': 'room_update', 'action': 'update', 'room': room_info}
                )

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
    def delete_room_force(self, room_id):
        try:
            Room.objects.get(id=room_id).delete()
        except Room.DoesNotExist:
            pass

    @database_sync_to_async
    def confirm_user(self, user, room_id):
        try:
            room = Room.objects.get(id=room_id)
            member = Member.objects.get(user=user, room=room)
            member.is_confirmed = True
            member.save()
        except Exception:
            pass

    @database_sync_to_async
    def get_confirmation_status(self, room_id):
        try:
            room = Room.objects.get(id=room_id)
            total = room.members.count()
            confirmed = room.members.filter(is_confirmed=True).count()
            return {'total': total, 'confirmed': confirmed}
        except Exception:
            return {'total': 0, 'confirmed': 0}