from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    win_num = models.IntegerField(default=0)
    lose_num = models.IntegerField(default=0)
    
    friends = models.ManyToManyField('self', blank=True)
    def __str__(self):
        return self.username

class FriendRequest(models.Model):
    from_user = models.ForeignKey(User, related_name='sent_friend_requests', on_delete=models.CASCADE)
    to_user = models.ForeignKey(User, related_name='received_friend_requests', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.from_user} -> {self.to_user}"
    
class WordSet(models.Model):
    main_word = models.CharField(max_length=100)
    wolf_word = models.CharField(max_length=100)
    category = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"{self.main_word} / {self.wolf_word}"

class Question(models.Model):
    text = models.CharField(max_length=200)
    category = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return self.text

class Room(models.Model):
    room_name = models.CharField(max_length=50)
    discussion_time = models.IntegerField(default=3, help_text="討論時間（分）")
    category = models.CharField(max_length=50, default='all', help_text="お題のカテゴリ")
    
    host = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='hosted_rooms')
    
    class Status(models.TextChoices):
        WAITING = 'waiting', '待機中'
        PLAYING = 'playing', 'プレイ中'
        FINISHED = 'finished', '終了'
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.WAITING
    )

    word_set = models.ForeignKey(WordSet, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.room_name} ({self.status})"

class RoomQuestion(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='questions')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)

    order = models.IntegerField()

    def __str__(self):
        return f"{self.room} - Q{self.order}"

class Member(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='members')

    class Role(models.TextChoices):
        WOLF = 'wolf', '狼'
        CITIZEN = 'citizen', '市民'
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CITIZEN
    )

    word = models.CharField(max_length=100, blank=True)
    vote_target = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='voted_by'
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.user.username} in {self.room.room_name}"
