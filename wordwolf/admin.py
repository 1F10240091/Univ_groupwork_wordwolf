from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, WordSet, Question, Room, Member, RoomQuestion

# カスタムユーザーモデルの設定
# 標準のUserAdminを継承し、追加したフィールド(win_num, lose_num)を編集できるようにします
class CustomUserAdmin(UserAdmin):
    model = User
    # ユーザー編集画面のフィールド設定に追加
    fieldsets = UserAdmin.fieldsets + (
        ('Game Stats', {'fields': ('win_num', 'lose_num')}),
    )
    # ユーザー一覧画面での表示項目
    list_display = ['username', 'email', 'win_num', 'lose_num', 'is_staff', 'is_active']

# Userモデルを登録
admin.site.register(User, CustomUserAdmin)

# その他のモデルを登録（一覧で見やすいようにlist_displayなどを設定）

@admin.register(WordSet)
class WordSetAdmin(admin.ModelAdmin):
    list_display = ('main_word', 'wolf_word', 'category')
    list_filter = ('category',)
    search_fields = ('main_word', 'wolf_word')

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'category')
    list_filter = ('category',)

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('room_name', 'status', 'max_user_num', 'created_at')
    list_filter = ('status',)
    search_fields = ('room_name',)

@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'room', 'role', 'joined_at')
    list_filter = ('room', 'role')

# RoomQuestionは単純な中間テーブルに近いのでシンプルに登録
admin.site.register(RoomQuestion)