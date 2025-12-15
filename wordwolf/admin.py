from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from django import forms
import json
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
    change_list_template = "admin/wordwolf/wordset/change_list.html"

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('import-json/', self.admin_site.admin_view(self.import_json), name='wordwolf_wordset_import_json'),
        ]
        return my_urls + urls

    def import_json(self, request):
        # デフォルトファイルを読み込む
        import os
        from django.conf import settings
        file_path = os.path.join(settings.BASE_DIR, 'wordwolf', 'fixtures', 'words,json')
        
        try:
            with open(file_path, 'rb') as f:
                content = f.read()

            if isinstance(content, bytes):
                try:
                    text = content.decode('utf-8')
                except UnicodeDecodeError:
                    try:
                        text = content.decode('cp932')
                    except UnicodeDecodeError:
                        raise ValueError("対応していないエンコーディングです。UTF-8またはShift-JISで保存してください。")
            else:
                text = content

            data = json.loads(text)
            
            # リスト形式であることを確認
            if not isinstance(data, list):
                raise ValueError("JSONデータはリスト形式である必要があります。")

            count = 0
            for item in data:
                # 必要なキーが存在するか確認
                if 'main_word' in item and 'wolf_word' in item:
                    obj, created = WordSet.objects.get_or_create(
                        main_word=item.get('main_word'),
                        wolf_word=item.get('wolf_word'),
                        defaults={'category': item.get('category', '')}
                    )
                    if created:
                        count += 1
            
            self.message_user(request, f"{count} 件のデータをインポートしました。")
        except Exception as e:
            self.message_user(request, f"エラーが発生しました: {e}", level=messages.ERROR)
        
        return redirect("..")

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